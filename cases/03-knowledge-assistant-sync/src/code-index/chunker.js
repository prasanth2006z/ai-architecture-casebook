'use strict';
/**
 * Code chunker for a Node.js backend (JavaScript and TypeScript).
 *
 * One changed file in -> a list of chunks out:
 *   - "function": top-level functions, arrow functions assigned to a
 *                 const, exports.x = function ..., module.exports = {...}
 *                 members, class methods, object-literal methods
 *   - "route":    Express-style router.post('/path', ...handlers)
 *   - "class":    class outline (JSDoc, fields, tiny methods, signatures)
 *   - "file":     file outline (imports, exports, small top-level code,
 *                 tiny functions)
 * Long functions are split at top-level statements ("#partN").
 *
 * Every chunk has a stable key and a hash of its CODE ONLY (never the
 * commit), so an unchanged function keeps its hash across commits.
 * Each chunk also records calls, tables and relative imports.
 *
 * Parser: the TypeScript compiler API. It parses .js/.cjs/.mjs/.jsx and
 * .ts/.tsx without type-checking and is a single pure-JS dependency.
 */
const crypto = require('node:crypto');
const path = require('node:path');
const ts = require('typescript');

const TINY_LINES = 4;          // fold into file/class outline
const MAX_LINES = 150;         // split longer functions into parts
const HTTP_METHODS = new Set(['get', 'post', 'put', 'patch', 'delete', 'all', 'options', 'head']);
const SQL_TABLE = /\b(?:from|join|into|update)\s+["`]?([a-zA-Z_][\w.]*)/gi;
const LOOKS_LIKE_SQL = /^\s*(select|insert|update|delete|with)\b[\s\S]*\b(from|into|set|join)\b/i;
const ENTITY_DECORATORS = new Set(['Entity', 'Table']);   // TypeORM, sequelize-typescript
const TABLE_CALLS = new Set(['knex', 'db', 'from', 'table', 'into', 'withSchema']);

const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');

function scriptKind(file) {
  const ext = path.extname(file).toLowerCase();
  return { '.ts': ts.ScriptKind.TS, '.tsx': ts.ScriptKind.TSX, '.jsx': ts.ScriptKind.JSX }[ext]
    || ts.ScriptKind.JS;
}

/** Module = directory, e.g. "src/services/claims". */
function moduleOf(file) {
  return path.posix.dirname(file.split(path.sep).join('/'));
}

function linesOf(sf, node) {
  const s = sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
  const e = sf.getLineAndCharacterOfPosition(node.getEnd()).line + 1;
  return [s, e];
}

function jsDocOf(sf, node) {
  const ranges = ts.getLeadingCommentRanges(sf.text, node.getFullStart()) || [];
  const docs = ranges.map((r) => sf.text.slice(r.pos, r.end)).filter((c) => c.startsWith('/**'));
  return docs.length ? docs[docs.length - 1] : '';
}

function hasExport(node) {
  return !!(ts.canHaveModifiers(node) && (ts.getModifiers(node) || [])
    .some((m) => m.kind === ts.SyntaxKind.ExportKeyword));
}

function calleeName(expr, sf) {
  // Flatten a.b(...).c.d(...) into [a, b, c, d]; report root.first
  // ("this.pool.query" -> "pool.query", "db(...).where(...).first()" -> "db.where").
  if (ts.isIdentifier(expr)) return expr.text;
  if (!ts.isPropertyAccessExpression(expr)) return null;
  const segs = [];
  let n = expr;
  for (;;) {
    if (ts.isPropertyAccessExpression(n)) { segs.unshift(n.name.text); n = n.expression; }
    else if (ts.isCallExpression(n)) n = n.expression;
    else break;
  }
  const root = ts.isIdentifier(n) ? n.text
    : n.kind === ts.SyntaxKind.ThisKeyword ? 'this' : null;
  if (root === 'this') return segs.length > 1 ? `${segs[0]}.${segs[1]}` : `this.${segs[0]}`;
  return root ? `${root}.${segs[0]}` : segs.join('.');
}

function stringText(node) {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (ts.isTemplateExpression(node)) {
    return [node.head.text, ...node.templateSpans.map((s) => s.literal.text)].join(' ? ');
  }
  return null;
}

/** Calls, tables and relative imports used inside a node. */
function scan(node, sf) {
  const calls = new Set();
  const tables = new Set();
  const imports = new Set();
  const visit = (n) => {
    if (ts.isCallExpression(n)) {
      const name = calleeName(n.expression, sf);
      if (name) calls.add(name);
      const last = name ? name.split('.').pop() : '';
      const arg = n.arguments[0];
      if (TABLE_CALLS.has(last) && arg && ts.isStringLiteral(arg)) tables.add(arg.text);
      if (name && /^prisma\.[a-zA-Z]/.test(name)) {
        tables.add(name.split('.')[1]);                  // Prisma model, e.g. prisma.claim.update
      }
      if (ts.isDecorator(n.parent) && ENTITY_DECORATORS.has(name) && arg) {
        if (ts.isStringLiteral(arg)) tables.add(arg.text);
        else if (ts.isObjectLiteralExpression(arg)) {
          const t = arg.properties.find((p) => p.name && ['name', 'tableName'].includes(p.name.getText(sf)));
          if (t && ts.isPropertyAssignment(t) && ts.isStringLiteral(t.initializer)) tables.add(t.initializer.text);
        }
      }
      if (name === 'require' && arg && ts.isStringLiteral(arg) && arg.text.startsWith('.')) {
        imports.add(arg.text);
      }
    }
    if (ts.isImportDeclaration(n) && ts.isStringLiteral(n.moduleSpecifier)
        && n.moduleSpecifier.text.startsWith('.')) {
      imports.add(n.moduleSpecifier.text);
    }
    if (ts.isPropertyAssignment(n) && n.name && n.name.getText(sf) === 'tableName'
        && ts.isStringLiteral(n.initializer)) {
      tables.add(n.initializer.text);
    }
    const s = stringText(n);
    if (s && LOOKS_LIKE_SQL.test(s)) for (const m of s.matchAll(SQL_TABLE)) tables.add(m[1].toLowerCase());
    ts.forEachChild(n, visit);
  };
  visit(node);
  return { calls: [...calls].sort(), tables: [...tables].sort(), imports: [...imports].sort() };
}

function signatureOf(fnNode, sf, nameForArrow) {
  const body = fnNode.body;
  const end = body ? body.getStart(sf) : fnNode.getEnd();
  let sig = sf.text.slice(fnNode.getStart(sf), end).trim().replace(/\s+/g, ' ');
  if (nameForArrow) sig = `${nameForArrow} = ${sig}`;
  return sig.replace(/\s*=>\s*$/, ' =>');
}

function paramsOf(fnNode, sf) {
  return '(' + fnNode.parameters.map((p) => p.name.getText(sf)).join(', ') + ')';
}

function isFunctionLike(n) {
  return n && (ts.isArrowFunction(n) || ts.isFunctionExpression(n));
}

function header(file, owner, symbol, commit, part) {
  return `// path: ${file}\n// ${owner ? `in: ${owner}  ` : ''}symbol: ${symbol}\n`
    + (part ? `// part: ${part}\n` : '') + `// commit: ${commit}\n`;
}

/**
 * @param {string} file    repo-relative path
 * @param {string} source  file contents
 * @param {string} commit  commit SHA being indexed (header only)
 */
function chunkFile(file, source, commit) {
  const sf = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, scriptKind(file));
  const module = moduleOf(file);
  const chunks = [];
  const outline = [];          // file outline lines
  const exported = new Set();

  const base = (extra) => ({ path: file, module, ...extra });

  function emitFunction({ symbol, owner, fnNode, stmtNode, isExported, outlineSink }) {
    const doc = jsDocOf(sf, stmtNode);
    const code = (doc ? doc + '\n' : '') + stmtNode.getText(sf);
    const [s, e] = linesOf(sf, stmtNode);
    const sig = signatureOf(fnNode, sf, ts.isArrowFunction(fnNode) || ts.isFunctionExpression(fnNode) ? symbol.split('.').pop() : null);
    if (e - s + 1 <= TINY_LINES) {
      const indent = outlineSink === outline ? '' : '  ';
      outlineSink.push(indent + stmtNode.getText(sf).replace(/\s+/g, ' '));
      return;
    }
    const meta = scan(stmtNode, sf);
    const common = base({ kind: 'function', symbol, doc, signature: sig, exported: !!isExported, ...meta });
    const body = fnNode.body;
    const key = `${file}#${symbol}${paramsOf(fnNode, sf)}`;
    if (e - s + 1 <= MAX_LINES || !body || !ts.isBlock(body)) {
      chunks.push({ ...common, key, text: header(file, owner, symbol, commit) + code,
        hash: sha(code), lines: [s, e] });
      return;
    }
    const groups = [];
    let cur = [];
    let start = null;
    for (const st of body.statements) {
      const [a, b] = linesOf(sf, st);
      if (start === null) start = a;
      if (cur.length && b - start + 1 > MAX_LINES) { groups.push(cur); cur = []; start = a; }
      cur.push(st);
    }
    if (cur.length) groups.push(cur);
    groups.forEach((g, i) => {
      const partCode = g.map((st) => st.getText(sf)).join('\n');
      const text = header(file, owner, symbol, commit, `${i + 1}/${groups.length}`)
        + (doc && i === 0 ? doc + '\n' : '') + `${sig} {  // part ${i + 1}\n${partCode}\n}`;
      chunks.push({ ...common, key: `${key}#part${i + 1}`, text, hash: sha(partCode),
        lines: [linesOf(sf, g[0])[0], linesOf(sf, g[g.length - 1])[1]] });
    });
  }

  function emitObjectMembers(objName, obj, isExported) {
    for (const p of obj.properties) {
      const name = p.name ? p.name.getText(sf) : null;
      if (!name) continue;
      if (ts.isMethodDeclaration(p)) {
        emitFunction({ symbol: `${objName}.${name}`, owner: objName, fnNode: p, stmtNode: p,
          isExported, outlineSink: outline });
      } else if (ts.isPropertyAssignment(p) && isFunctionLike(p.initializer)) {
        emitFunction({ symbol: `${objName}.${name}`, owner: objName, fnNode: p.initializer, stmtNode: p,
          isExported, outlineSink: outline });
      }
      const isFn = ts.isMethodDeclaration(p)
        || (ts.isPropertyAssignment(p) && isFunctionLike(p.initializer));
      if (isExported && isFn) exported.add(objName === 'exports' ? name : `${objName}.${name}`);
    }
  }

  function emitClass(cls, isExported) {
    const name = cls.name ? cls.name.text : 'default';
    const doc = jsDocOf(sf, cls);
    const head = sf.text.slice(cls.getStart(sf), cls.members.pos).trim().replace(/\s+/g, ' ');
    const lines = [doc, head];
    const sigs = [];
    for (const m of cls.members) {
      if ((ts.isMethodDeclaration(m) || ts.isConstructorDeclaration(m)
          || ts.isGetAccessorDeclaration(m) || ts.isSetAccessorDeclaration(m)) && m.body) {
        const mname = ts.isConstructorDeclaration(m) ? 'constructor' : m.name.getText(sf);
        sigs.push('  ' + signatureOf(m, sf) + ';');
        emitFunction({ symbol: `${name}.${mname}`, owner: name, fnNode: m, stmtNode: m,
          isExported, outlineSink: lines });
      } else if (ts.isPropertyDeclaration(m) && isFunctionLike(m.initializer)) {
        const mname = m.name.getText(sf);
        sigs.push(`  ${mname} = ${signatureOf(m.initializer, sf)};`);
        emitFunction({ symbol: `${name}.${mname}`, owner: name, fnNode: m.initializer, stmtNode: m,
          isExported, outlineSink: lines });
      } else {
        lines.push('  ' + m.getText(sf).replace(/\s+/g, ' '));
      }
    }
    lines.push('  // methods:', ...sigs, '}');
    const code = lines.filter(Boolean).join('\n');
    chunks.push(base({ kind: 'class', key: `${file}#${name}`, symbol: name, doc,
      signature: head.replace(/\s*\{$/, ''), exported: !!isExported,
      text: header(file, null, name, commit) + code, hash: sha(code),
      lines: linesOf(sf, cls), ...scan(cls, sf) }));
    if (isExported) exported.add(name);
  }

  function routeOf(expr) {
    // router.post('/claims/:id/approve', auth, handler)  |  app.get(...)
    if (!ts.isCallExpression(expr) || !ts.isPropertyAccessExpression(expr.expression)) return null;
    const method = expr.expression.name.text;
    const target = expr.expression.expression;
    const arg = expr.arguments[0];
    if (!HTTP_METHODS.has(method) || !arg || !ts.isStringLiteral(arg)) return null;
    if (method === 'get' && expr.arguments.length < 2) return null;  // app.get('setting')
    return { verb: method.toUpperCase(), route: arg.text, on: target.getText(sf) };
  }

  for (const st of sf.statements) {
    // import / require lines and other small statements go to the outline
    if (ts.isFunctionDeclaration(st) && st.body) {
      const name = st.name ? st.name.text : 'default';
      emitFunction({ symbol: name, fnNode: st, stmtNode: st, isExported: hasExport(st), outlineSink: outline });
      if (hasExport(st)) exported.add(name);
      continue;
    }
    if (ts.isClassDeclaration(st)) { emitClass(st, hasExport(st)); continue; }

    if (ts.isVariableStatement(st)) {
      let handled = false;
      for (const d of st.declarationList.declarations) {
        const name = d.name.getText(sf);
        if (isFunctionLike(d.initializer)) {
          emitFunction({ symbol: name, fnNode: d.initializer,
            stmtNode: st.declarationList.declarations.length === 1 ? st : d,
            isExported: hasExport(st), outlineSink: outline });
          handled = true;
        } else if (d.initializer && ts.isObjectLiteralExpression(d.initializer)
            && d.initializer.properties.some((p) => ts.isMethodDeclaration(p)
              || (ts.isPropertyAssignment(p) && isFunctionLike(p.initializer)))) {
          emitObjectMembers(name, d.initializer, hasExport(st));
          handled = true;
        } else if (d.initializer && ts.isClassExpression(d.initializer)) {
          emitClass(d.initializer, hasExport(st));
          handled = true;
        }
        if (hasExport(st)) exported.add(name);
      }
      if (!handled) outline.push(st.getText(sf).replace(/\s+/g, ' ').slice(0, 240));
      continue;
    }

    if (ts.isExpressionStatement(st)) {
      const ex = st.expression;
      const r = routeOf(ex);
      if (r) {
        const symbol = `${r.verb} ${r.route}`;
        const doc = jsDocOf(sf, st);
        const code = (doc ? doc + '\n' : '') + st.getText(sf);
        const handlers = ex.arguments.slice(1)
          .filter((a) => ts.isIdentifier(a) || ts.isPropertyAccessExpression(a))
          .map((a) => a.getText(sf));
        const meta = scan(st, sf);
        chunks.push(base({ kind: 'route', key: `${file}#ROUTE ${symbol}`, symbol, doc,
          signature: `${r.on}.${r.verb.toLowerCase()}('${r.route}')`, exported: true,
          text: header(file, r.on, symbol, commit) + code, hash: sha(code),
          lines: linesOf(sf, st), ...meta,
          calls: [...new Set([...meta.calls, ...handlers])]
            .filter((c) => c !== `${r.on}.${r.verb.toLowerCase()}`).sort() }));
        continue;
      }
      // module.exports = {...} | exports.x = fn | module.exports.x = fn
      if (ts.isBinaryExpression(ex) && ex.operatorToken.kind === ts.SyntaxKind.EqualsToken) {
        const left = ex.left.getText(sf);
        if (/^(module\.)?exports(\.\w+)?$/.test(left)) {
          const right = ex.right;
          const short = left.replace(/^module\./, '').replace(/^exports\.?/, '') || 'module.exports';
          if (isFunctionLike(right)) {
            emitFunction({ symbol: short, fnNode: right, stmtNode: st, isExported: true, outlineSink: outline });
            exported.add(short);
            continue;
          }
          if (ts.isObjectLiteralExpression(right)) {
            emitObjectMembers('exports', right, true);
            for (const p of right.properties) {
              if (ts.isShorthandPropertyAssignment(p)) exported.add(p.name.text);
              else if (ts.isPropertyAssignment(p) && ts.isIdentifier(p.initializer)) exported.add(p.name.getText(sf));
            }
            outline.push(st.getText(sf).replace(/\s+/g, ' ').slice(0, 240));
            continue;
          }
          if (ts.isClassExpression(right)) { emitClass(right, true); continue; }
          exported.add(short);
        }
      }
    }
    outline.push(st.getText(sf).replace(/\s+/g, ' ').slice(0, 240));
  }

  // Functions exported later (module.exports = { fn }, export { fn }) count as exported.
  for (const st of sf.statements) {
    if (ts.isExportDeclaration(st) && st.exportClause && ts.isNamedExports(st.exportClause)) {
      st.exportClause.elements.forEach((e) => exported.add(e.name.text));
    }
  }
  for (const c of chunks) {
    const root = c.symbol.startsWith('exports.') ? c.symbol.slice(8) : c.symbol.split('.')[0];
    if (exported.has(c.symbol) || exported.has(root)) c.exported = true;
  }

  // File outline: imports, constants, tiny functions, export list.
  const outlineCode = [...outline, `// exports: ${[...exported].sort().join(', ') || '(none)'}`].join('\n');
  chunks.push(base({ kind: 'file', key: `${file}#<file>`, symbol: path.posix.basename(file), doc: '',
    signature: '', exported: false, text: header(file, null, '<file>', commit) + outlineCode,
    hash: sha(outlineCode), lines: [1, sf.getLineAndCharacterOfPosition(sf.getEnd()).line + 1],
    ...scan(sf, sf), exports: [...exported].sort() }));
  return chunks;
}

/** stored: {key: hash} for one file. Returns what to upsert and delete. */
function planFileUpdate(stored, newChunks) {
  const keys = new Set(newChunks.map((c) => c.key));
  return {
    upserts: newChunks.filter((c) => stored[c.key] !== c.hash),
    deletes: Object.keys(stored).filter((k) => !keys.has(k)).sort(),
  };
}

/** Changes only when some chunk in the module changes. */
function moduleInputHash(moduleChunks) {
  return sha(moduleChunks.map((c) => `${c.key}:${c.hash}`).sort().join('\n'));
}

/** Compact input for the module summary prompt: no function bodies. */
function moduleDigest(module, moduleChunks) {
  const out = [`MODULE ${module}`];
  const sorted = [...moduleChunks].sort((a, b) => a.key.localeCompare(b.key));
  const oneLine = (s, n) => s.replace(/\s+/g, ' ').slice(0, n);
  for (const c of sorted) {
    if (c.key.includes('#part') && !c.key.endsWith('#part1')) continue;
    if (c.kind === 'file') {
      out.push(`\nFILE ${c.path}`);
      if (c.exports.length) out.push(`  exports: ${c.exports.join(', ')}`);
      if (c.imports.length) out.push(`  imports: ${c.imports.join(', ')}`);
    } else if (c.kind === 'route') {
      out.push(`  ROUTE ${c.symbol}  handlers/calls: ${c.calls.slice(0, 10).join(', ')}`);
    } else if (c.kind === 'class' || c.exported) {
      out.push(`  ${c.kind.toUpperCase()} ${oneLine(c.signature, 160)}`);
      if (c.doc) out.push(`    doc: ${oneLine(c.doc, 300)}`);
      if (c.calls.length && c.kind !== 'class') out.push(`    calls: ${c.calls.slice(0, 15).join(', ')}`);
      if (c.tables.length) out.push(`    tables: ${c.tables.join(', ')}`);
    }
  }
  return out.join('\n');
}

const SUMMARY_PROMPT = `You are documenting one module of the ClaimFlow backend (Node.js)
for new team members. Use only the digest below. Do not guess.
Answer in exactly these sections, short:
Purpose (2 sentences) | HTTP routes | Main exported functions | Tables read/written |
Statuses set | Modules it depends on | Notes
If something is not visible in the digest, write "not visible".

{digest}`;

module.exports = {
  chunkFile, planFileUpdate, moduleInputHash, moduleDigest, moduleOf,
  SUMMARY_PROMPT, TINY_LINES, MAX_LINES,
};
