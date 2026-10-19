"""Table images for Case 03 (Medium has no tables). Uses the Case 02 table style."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw  # noqa: E402
import tables  # noqa: E402
from draw import RED, AMBER, GREEN, PURPLE, BLUE  # noqa: E402

OUT = os.path.dirname(HERE)
tables.OUT = OUT
draw.OUT = OUT


def t1():
    verdict = lambda t: GREEN if t.startswith("Chosen") else AMBER if t.startswith("Docs") else RED
    tables.table(
        "t1-options.png", "Three ways to give the assistant its knowledge",
        ["Option", "How it stays current", "Limits", "Verdict"],
        [["Hand-built summary (today)", "Someone re-summarises when they remember",
          "Stale by default; too big to fit; no citations", "Replace"],
         ["Managed connector (e.g. Gemini Enterprise for Confluence)", "Full and incremental sync run by the platform",
          "Covers docs well; no Bitbucket connector listed; schema needs more than text search", "Docs only"],
         ["Own per-source indexes", "Webhooks and polling per source, plus nightly reconcile",
          "We run the pipelines", "Chosen"]],
        [(0.27, 0), (0.27, 0), (0.30, 0), (0.16, 0)], chips={3: verdict})


def t2():
    tables.table(
        "t2-representations.png", "Each source is stored in the form its questions need",
        ["Source", "Unit", "Kept with each unit", "Reached through"],
        [["Confluence", "Page section", "Title, space, labels, feature key, page version, restrictions",
          "Hybrid search (keywords + vectors)"],
         ["Code", "Function, class or HTTP route; short per-module summary", "File path, symbol, prod commit, calls, tables",
          "Hybrid search; summary rebuilt only when the module changes"],
         ["Schema", "Table, column, foreign key, status value", "Type, comment, snapshot time",
          "Tools: describe_table, find_join_path, list_status_values"],
         ["Other teams", "Published contracts only", "API spec or event schema version",
          "Search; pointer to the owning team"]],
        [(0.15, 0), (0.25, 0), (0.30, 0), (0.30, 0)], accent=BLUE)


def t3():
    tables.table(
        "t3-metrics.png", "Four numbers to watch",
        ["Metric", "Definition", "Why"],
        [["Freshness lag", "Time from a change in a source to the index, per source", "Is the assistant current?"],
         ["Citation rate", "Share of answers citing at least one page, file or table", "Can people check it?"],
         ["SQL validity", "Share of generated queries that pass the guard first time", "Does it know today's schema?"],
         ["Golden-set pass rate", "Real questions answered with the expected sources", "Did the last sync break anything?"]],
        [(0.24, 0), (0.48, 0), (0.28, 0)], accent=PURPLE)


if __name__ == "__main__":
    for fn in (t1, t2, t3):
        fn()
    print("ok")
