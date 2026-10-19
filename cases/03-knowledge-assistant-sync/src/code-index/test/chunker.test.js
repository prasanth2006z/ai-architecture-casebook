'use strict';
// Run: npm install && npm test
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const {
  chunkFile, planFileUpdate, moduleInputHash, moduleDigest, MAX_LINES,
} = require('../chunker');

const FX = path.join(__dirname, 'fixtures');
const read = (f) => fs.readFileSync(path.join(FX, f), 'utf8');
const ROUTES = 'src/routes/claims.routes.js';
const SERVICE = 'src/services/approval.service.js';
const TS = 'src/services/rejection.service.ts';

const byKey = (cs) => Object.fromEntries(cs.map((c) => [c.key, c]));
const svc = (src = read('approval.service.js'), commit = 'a1b2c3d') => chunkFile(SERVICE, src, commit);

test('express routes become route chunks linked to their handlers', () => {
  const cs = chunkFile(ROUTES, read('claims.routes.js'), 'a1b2c3d');
  const k = byKey(cs);
  const post = k[`${ROUTES}#ROUTE POST /claims/:id/approve-partial`];
  assert.equal(post.kind, 'route');
  assert.ok(post.doc.includes('CLM-482'));
  assert.ok(post.calls.includes('approval.approvePartial'));
  assert.ok(post.calls.includes('requireRole'));
  const get = k[`${ROUTES}#ROUTE GET /claims/:id`];
  assert.ok(get.calls.includes('approval.getClaim'));
  assert.ok(k[`${ROUTES}#<file>`].imports.includes('../services/approval.service'));
});

test('functions and arrow functions get their own chunks; tiny ones fold into the file outline', () => {
  const k = byKey(svc());
  assert.deepEqual(Object.keys(k).sort(), [
    `${SERVICE}#<file>`,
    `${SERVICE}#approvePartial(claimId, decisions)`,
    `${SERVICE}#getClaim(req, res)`,
  ]);
  const file = k[`${SERVICE}#<file>`];
  assert.ok(file.text.includes('isFinal'));
  assert.deepEqual(file.exports, ['approvePartial', 'getClaim', 'isFinal']);
  assert.equal(file.module, 'src/services');
});

test('header, JSDoc, calls and tables (knex and raw SQL)', () => {
  const k = byKey(svc());
  const ap = k[`${SERVICE}#approvePartial(claimId, decisions)`];
  assert.ok(ap.text.startsWith(`// path: ${SERVICE}`));
  assert.ok(ap.text.includes('commit: a1b2c3d'));
  assert.ok(ap.doc.includes('CLM-482'));
  assert.deepEqual(ap.tables, ['claim_items', 'claims']);
  assert.ok(ap.calls.includes('db'));
  const gc = k[`${SERVICE}#getClaim(req, res)`];
  assert.deepEqual(gc.tables, ['claim_status_history', 'claims']);
  assert.ok(gc.calls.includes('pool.query'));
});

test('typescript class: outline chunk plus method chunks', () => {
  const k = byKey(chunkFile(TS, read('rejection.service.ts'), 'a1b2c3d'));
  const cls = k[`${TS}#RejectionService`];
  assert.equal(cls.kind, 'class');
  assert.ok(cls.text.includes('constructor(private readonly pool: Pool) {}'));
  assert.ok(cls.text.includes('get name()'));
  const rej = k[`${TS}#RejectionService.reject(claimId, reason)`];
  assert.deepEqual(rej.tables, ['claims']);
  assert.ok(rej.calls.includes('pool.query') && rej.calls.includes('audit.log'));
  assert.ok(rej.exported);
});

test('same code under a new commit: nothing to do', () => {
  const stored = Object.fromEntries(svc(undefined, 'a1b2c3d').map((c) => [c.key, c.hash]));
  const { upserts, deletes } = planFileUpdate(stored, svc(undefined, 'ffff999'));
  assert.deepEqual([upserts.length, deletes.length], [0, 0]);
});

test('one function changed: only that chunk is upserted', () => {
  const stored = Object.fromEntries(svc().map((c) => [c.key, c.hash]));
  const v2 = read('approval.service.js').replace('res.json(rows[0]);', 'res.json(rows[0] ?? null);');
  const { upserts, deletes } = planFileUpdate(stored, svc(v2));
  assert.deepEqual(upserts.map((u) => u.symbol), ['getClaim']);
  assert.deepEqual(deletes, []);
});

test('function deleted: its chunk is deleted and the file outline updated', () => {
  const stored = Object.fromEntries(svc().map((c) => [c.key, c.hash]));
  const src = read('approval.service.js');
  const start = src.indexOf('const getClaim');
  const end = src.indexOf('};', start) + 3;
  const v3 = (src.slice(0, start) + src.slice(end)).replace('getClaim, ', '');
  const { upserts, deletes } = planFileUpdate(stored, svc(v3));
  assert.deepEqual(deletes, [`${SERVICE}#getClaim(req, res)`]);
  assert.deepEqual(upserts.map((u) => u.kind), ['file']);
});

test('comment between functions does not change the module hash', () => {
  const v2 = read('approval.service.js').replace('const getClaim', '// TODO: paginate\nconst getClaim');
  assert.equal(moduleInputHash(svc(v2)), moduleInputHash(svc()));
  const v3 = read('approval.service.js').replace('.first();', '.first(); // pick one');
  assert.notEqual(moduleInputHash(svc(v3)), moduleInputHash(svc()));
});

test('long function is split into parts that repeat the signature', () => {
  const body = Array.from({ length: MAX_LINES + 40 }, (_, i) => `  step${i}();`).join('\n');
  const src = `/** Big job. */\nexport async function run(batch) {\n${body}\n}\n`;
  const parts = chunkFile('src/jobs/big.js', src, 'c').filter((c) => c.kind === 'function');
  assert.equal(parts.length, 2);
  assert.ok(parts[0].key.endsWith('#part1') && parts[1].key.endsWith('#part2'));
  assert.ok(parts.every((p) => p.text.includes('function run(batch)')));
});

test('module digest has routes, signatures, calls and tables but no bodies', () => {
  const all = [...svc(), ...chunkFile(TS, read('rejection.service.ts'), 'a')];
  const d = moduleDigest('src/services', all);
  assert.ok(d.includes('FUNCTION async function approvePartial(claimId, decisions)'));
  assert.ok(d.includes('tables: claim_items, claims'));
  assert.ok(d.includes('CLASS export class RejectionService'));
  assert.ok(!d.includes('approved_amount: d.amount'));
});

test('index-repo diff: modified, renamed and deleted files', () => {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'ci-'));
  const g = (...a) => execFileSync('git', ['-C', repo, ...a], { encoding: 'utf8' });
  g('init', '-q'); g('config', 'user.email', 't@t'); g('config', 'user.name', 't');
  fs.mkdirSync(path.join(repo, 'src/services'), { recursive: true });
  fs.mkdirSync(path.join(repo, 'src/routes'), { recursive: true });
  fs.writeFileSync(path.join(repo, SERVICE), read('approval.service.js'));
  fs.writeFileSync(path.join(repo, ROUTES), read('claims.routes.js'));
  fs.writeFileSync(path.join(repo, 'src/services/old.js'), 'module.exports = 1;\n');
  fs.writeFileSync(path.join(repo, 'src/services/approval.test.js'), 'test(1);\n');
  g('add', '.'); g('commit', '-qm', 'v1');
  const v1 = g('rev-parse', 'HEAD').trim();
  fs.writeFileSync(path.join(repo, SERVICE), read('approval.service.js').replace('rows[0]', 'rows[1]'));
  g('mv', ROUTES, 'src/routes/claim.routes.js');
  g('rm', '-q', 'src/services/old.js');
  g('commit', '-qam', 'v2');
  const out = execFileSync('node', [path.join(__dirname, '..', 'index-repo.js'), 'diff', repo, v1, 'HEAD'],
    { encoding: 'utf8' }).trim().split('\n').map((l) => JSON.parse(l));
  const ops = out.map((o) => `${o.op}:${o.path || o.touched.join(',')}`).sort();
  assert.deepEqual(ops, [
    'delete_file:src/routes/claims.routes.js',
    'delete_file:src/services/old.js',
    'file:src/routes/claim.routes.js',
    `file:${SERVICE}`,
    'modules:src/routes,src/services',
  ]);
  fs.rmSync(repo, { recursive: true, force: true });
});

test('tables from Prisma, TypeORM entities and SQL; plain English strings ignored', () => {
  const src = `
import { Entity } from 'typeorm';
@Entity('claim_documents')
export class ClaimDocument { id!: string; }

export async function load(id) {
  const c = await prisma.claim.findUnique({ where: { id } });
  if (!c) throw new Error('Please update from the portal and join again');
  return prisma.reserve.findMany({ where: { claimId: id } });
}
`;
  const k = byKey(chunkFile('src/x.ts', src, 'c'));
  assert.deepEqual(k['src/x.ts#ClaimDocument'].tables, ['claim_documents']);
  assert.deepEqual(k['src/x.ts#load(id)'].tables, ['claim', 'reserve']);
});
