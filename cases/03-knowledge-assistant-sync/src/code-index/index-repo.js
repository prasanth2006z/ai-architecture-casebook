#!/usr/bin/env node
'use strict';
/**
 * Produce chunks for a git ref, as JSON lines on stdout.
 *
 *   node index-repo.js full <repoDir> <ref>
 *       Every included file at <ref>. Use for the first load and the
 *       nightly reconcile. Reads blobs with `git show`, so it indexes
 *       exactly that ref (e.g. the commit deployed to production)
 *       without checking it out.
 *
 *   node index-repo.js diff <repoDir> <oldRef> <newRef>
 *       Only files changed between two refs (what the webhook sends).
 *
 * Output lines:
 *   {"op":"file","path":...,"chunks":[...]}    replace this file's chunks
 *   {"op":"delete_file","path":...}            drop all chunks of a file
 *   {"op":"modules","touched":[...]}           modules to re-check for summaries
 *
 * The loader compares each file's chunks with the stored {key: hash}
 * (planFileUpdate), embeds only the upserts, and deletes missing keys.
 */
const { execFileSync } = require('node:child_process');
const { chunkFile, moduleOf } = require('./chunker');

const INCLUDE = /\.(c|m)?(j|t)sx?$/;
const EXCLUDE = [
  /(^|\/)node_modules\//, /(^|\/)(dist|build|coverage|\.next)\//,
  /\.min\.js$/, /\.d\.ts$/,
];
const TESTS = [/\.(test|spec)\.(c|m)?(j|t)sx?$/, /(^|\/)__tests__\//];

const withTests = process.argv.includes('--with-tests');
const args = process.argv.slice(2).filter((a) => !a.startsWith('--'));

function git(repo, ...a) {
  return execFileSync('git', ['-C', repo, ...a], { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
}

function included(p) {
  if (!INCLUDE.test(p) || EXCLUDE.some((r) => r.test(p))) return false;
  return withTests || !TESTS.some((r) => r.test(p));
}

function emit(o) { process.stdout.write(JSON.stringify(o) + '\n'); }

function chunksAt(repo, ref, p) {
  const commit = git(repo, 'rev-parse', '--short', ref).trim();
  return chunkFile(p, git(repo, 'show', `${ref}:${p}`), commit);
}

function full(repo, ref) {
  const files = git(repo, 'ls-tree', '-r', '--name-only', ref).split('\n').filter(included);
  const touched = new Set();
  for (const p of files) {
    emit({ op: 'file', path: p, chunks: chunksAt(repo, ref, p) });
    touched.add(moduleOf(p));
  }
  emit({ op: 'modules', touched: [...touched].sort() });
}

function diff(repo, oldRef, newRef) {
  const lines = git(repo, 'diff', '--name-status', '-M', oldRef, newRef).split('\n').filter(Boolean);
  const touched = new Set();
  for (const line of lines) {
    const [status, a, b] = line.split('\t');
    if (status.startsWith('R')) {                       // renamed: a -> b
      if (included(a)) { emit({ op: 'delete_file', path: a }); touched.add(moduleOf(a)); }
      if (included(b)) { emit({ op: 'file', path: b, chunks: chunksAt(repo, newRef, b) }); touched.add(moduleOf(b)); }
    } else if (status === 'D') {
      if (included(a)) { emit({ op: 'delete_file', path: a }); touched.add(moduleOf(a)); }
    } else if (included(a)) {                           // A, M, T, C
      emit({ op: 'file', path: a, chunks: chunksAt(repo, newRef, a) });
      touched.add(moduleOf(a));
    }
  }
  emit({ op: 'modules', touched: [...touched].sort() });
}

const [cmd, repo, r1, r2] = args;
if (cmd === 'full' && repo && r1) full(repo, r1);
else if (cmd === 'diff' && repo && r1 && r2) diff(repo, r1, r2);
else {
  process.stderr.write('usage: index-repo.js full <repo> <ref> | diff <repo> <old> <new> [--with-tests]\n');
  process.exit(2);
}
