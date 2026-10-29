# ADR-003: Give each source its own representation

- **Status:** Accepted
- **Date:** 2026-11-02
- **Case:** 03 · Keeping a team knowledge assistant in sync (GCP)
- **Related:** ADR-001, ADR-005, ADR-007 (code chunking details); Case 01 · ADR-003 (section-based chunking), Case 01 · ADR-002 (access control in retrieval)

## Context

Prose, code and schema answer different questions and break differently when chunked the same way. Fixed-size chunks cut functions in half; embedding table definitions as text makes join questions and column checks unreliable.

## Decision

| Source | Unit | Metadata on each unit | Access |
|---|---|---|---|
| Confluence | Page section, with title, space, labels and feature key prepended | Page ID, version, last modified, restrictions | Hybrid search (keywords + vectors) |
| Code (Node.js) | Function, class or HTTP route (parsed, not split by line count); file outline; short per-module summary | File path, symbol, prod commit SHA, calls, tables, imports | Hybrid search; summary rebuilt only when that module changes (ADR-007) |
| Schema | Catalog: tables, columns, types, foreign keys, comments, status values from reference tables | Snapshot time | Tools: `describe_table`, `find_join_path` (shortest path over foreign keys), `list_status_values` |
| Other teams (Portal, Intake) | Published contracts only: API specs, event schemas, shared tables | Contract version | Search; answers point to the owning team for internals |

Data rules:

- **No customer rows.** Only structure and reference tables (allow-list) are read. Claims tables contain personal and medical data.
- **Permissions.** Confluence restrictions are stored on each chunk and applied as a retrieval filter for the asking user (same principle as Case 01 · ADR-002).

## Options considered

| Option | Why not chosen |
|---|---|
| One chunking strategy for everything | Breaks code and loses schema structure |
| Embed the schema DDL as text | Unreliable for joins and column validation |
| Index other teams' code too | We cannot keep it current or answer for it |

## Consequences

- Three indexers to maintain instead of one.
- Schema questions become exact (tool calls), not approximate (search).
- Reference-table allow-list must be maintained.

## Verification

- Golden-set questions per source type (ADR-006).
- Test: a user without access to a restricted page never receives chunks from it.
- Test: indexer never reads from tables outside the allow-list.
