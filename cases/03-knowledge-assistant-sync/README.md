# Case 03: Keeping a Team Knowledge Assistant in Sync

## medium/
- `post-03-knowledge-assistant-sync.md`: the post text (markdown)
- `images/`: upload these to Medium where each `![...]` appears
  - `00-cover.png`: cover, full width under the title; also the Story preview image
  - `01`–`08`: diagrams; `t1`–`t3`: tables as images
- `preview.html`: open in a browser to see the full post laid out

Medium setup
- Subtitle: A design case study: why a hand-built context goes stale, and how to keep an assistant current with code, docs and schema automatically.
- Topics: Artificial Intelligence, Software Architecture, Google Cloud, Machine Learning, Developer Tools

## repo/
Copy `repo/cases/03-knowledge-assistant-sync/` into `ai-architecture-casebook/cases/`.
- `design.md`: full technical design
- `adr/ADR-001` … `ADR-007`: decision records
- `diagrams/`: all images + the scripts that draw them
- `src/sql_guard.py` + tests (Python, sqlglot)
- `src/code-index/`: Node.js code chunker + tests (`npm install && npm test`)
