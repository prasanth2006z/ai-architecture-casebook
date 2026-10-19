"""Diagrams for Case 03: keeping a team knowledge assistant in sync.
Reuses the Case 02 style helpers. Run: python3 draw3.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw  # noqa: E402
from draw import (fig, box, arrow, note, diamond, INK, MUTED, GRAY, BLUE,  # noqa: E402
                  GREEN, AMBER, RED, PURPLE, BG)
from matplotlib.patches import FancyBboxPatch  # noqa: E402

OUT = os.path.dirname(HERE)
os.makedirs(OUT, exist_ok=True)
draw.OUT = OUT
save = draw.save
TEAL = ("#f0fdfa", "#0d9488")


def group(ax, x, y, w, h, label, ec, fc="#fafafa", ha="left"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=fc, ec=ec, lw=1.3, ls="--"))
    lx = x + 2 if ha == "left" else x + w - 2
    note(ax, lx, y + h - 2.5, label, fs=10, weight="bold", color=ec, ha=ha)


# 1. Today ---------------------------------------------------------------------
def d01():
    f, ax = fig(70, "Today: one hand-built context")
    # teams row
    note(ax, 3, 59, "THE CLAIMS JOURNEY", fs=10, weight="bold")
    box(ax, 3, 46, 26, 9, "Claims Portal", GRAY, sub="UI · portal team")
    box(ax, 35, 46, 34, 9, "Claims Intake", GRAY, sub="preprocessing · integration team")
    box(ax, 75, 46, 26, 9, "ClaimFlow", BLUE, bold=True, sub="backend · our team")
    arrow(ax, (29, 50.5), (35, 50.5))
    arrow(ax, (69, 50.5), (75, 50.5))
    # sources
    note(ax, 3, 37, "OUR SOURCES", fs=10, weight="bold")
    box(ax, 3, 24, 22, 9, "Confluence", GRAY, sub="specs · runbooks")
    box(ax, 3, 13, 22, 9, "Bitbucket", GRAY, sub="code · migrations")
    box(ax, 3, 2, 22, 9, "Database", GRAY, sub="~80 tables")
    # manual step
    box(ax, 36, 11, 26, 13, "Copy, paste,\nask ChatGPT to summarise", AMBER, fs=10)
    for y in (28.5, 17.5, 6.5):
        arrow(ax, (25, y), (36, 17.5), ls="--")
    box(ax, 70, 11, 20, 13, "One context\ndocument", AMBER, bold=True, fs=10.5)
    arrow(ax, (62, 17.5), (70, 17.5))
    box(ax, 98, 11, 19, 13, "Chat assistant", BLUE, bold=True, sub="new joiners · SQL")
    arrow(ax, (90, 17.5), (98, 17.5))
    ax.text(49, 31, "Who updates this,\nand when?", ha="center", va="center", fontsize=11,
            fontweight="bold", color=RED[1], linespacing=1.35)
    save(f, "01-today.png")


# 2. Drift timeline -----------------------------------------------------------
def d02():
    f, ax = fig(56, "CLM-482 ships on Tuesday. The context catches up weeks later.")
    y = 24
    ax.plot([6, 114], [y, y], color=GRAY[1], lw=3, solid_capstyle="round")
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "…", "+3 weeks"]
    xs = [8, 22, 36, 50, 64, 80, 104]
    for d, x in zip(days, xs):
        ax.plot([x, x], [y - 1, y + 1], color=GRAY[1], lw=2)
        note(ax, x, y - 4, d, fs=10, ha="center")
    # stale band
    ax.add_patch(FancyBboxPatch((22, y + 2.5), 82, 4, boxstyle="round,pad=0,rounding_size=1",
                                fc=RED[0], ec=RED[1], lw=1.2))
    note(ax, 63, y + 4.5, "assistant answers from the old version", fs=10, ha="center",
         color=RED[1], weight="bold")
    # release
    box(ax, 10, 33, 30, 12, "Release: CLM-482", BLUE, bold=True,
        sub="amount → claimed / approved_amount\nnew status PARTIALLY_APPROVED", fs=10.5)
    arrow(ax, (22, 33), (22, y + 7), BLUE[1])
    # thursday question
    box(ax, 44, 33, 34, 12, "Thursday: “SQL for stuck claims?”", GRAY, bold=True,
        sub="loud: uses claim_items.amount → error\nsilent: misses PARTIALLY_APPROVED", fs=10.5)
    arrow(ax, (50, 33), (50, y + 7), MUTED)
    # refresh
    box(ax, 88, 33, 28, 12, "Someone refreshes\nthe context", AMBER, fs=10.5)
    arrow(ax, (104, 33), (104, y + 7), AMBER[1])
    note(ax, 3, 8, "The silent failure is the dangerous one: the query runs, returns rows, and is wrong.",
         fs=10.5, style="italic")
    save(f, "02-drift.png")


# 3. Architecture --------------------------------------------------------------
def d03():
    f, ax = fig(99, "The design in one picture (Google Cloud)")
    # sources
    group(ax, 3, 52, 24, 33, "SOURCES", MUTED)
    box(ax, 5, 72, 20, 8, "Bitbucket", GRAY, bold=True, fs=10.5)
    box(ax, 5, 63, 20, 8, "Confluence", GRAY, bold=True, fs=10.5)
    box(ax, 5, 54, 20, 8, "DB read replica", GRAY, bold=True, fs=10.5)
    # triggers
    group(ax, 32, 52, 26, 33, "TRIGGERS", PURPLE[1])
    box(ax, 34, 72, 22, 8, "Webhook → Cloud Run", PURPLE, fs=9.5, sub="prod tag moved · HMAC checked")
    box(ax, 34, 63, 22, 8, "Scheduler · 15 min", PURPLE, fs=9.5, sub="CQL lastmodified")
    box(ax, 34, 54, 22, 8, "Migration deployed", PURPLE, fs=9.5, sub="+ nightly reconcile")
    for y0 in (76, 67, 58):
        arrow(ax, (25, y0), (34, y0))
    box(ax, 64, 63, 18, 9, "Pub/Sub", GRAY, bold=True, sub="source-changed", fs=10.5)
    for y0 in (76, 67, 58):
        arrow(ax, (56, y0), (64, 67.5))
    # indexers
    group(ax, 87, 52, 30, 33, "CLOUD RUN JOBS", BLUE[1])
    box(ax, 89, 72, 26, 8, "Docs indexer", BLUE, fs=10, sub="section chunks")
    box(ax, 89, 63, 26, 8, "Code indexer", BLUE, fs=10, sub="function · class · route")
    box(ax, 89, 54, 26, 8, "Schema indexer", BLUE, fs=10, sub="catalog + join graph")
    for y0 in (76, 67, 58):
        arrow(ax, (82, 67.5), (89, y0))
    # store
    box(ax, 72, 30, 45, 14, "Cloud SQL for PostgreSQL", TEAL, bold=True,
        sub="pgvector chunks · schema catalog · sync state · versions", fs=11)
    arrow(ax, (102, 52), (102, 44))
    # assistant
    box(ax, 3, 30, 26, 14, "Chat UI", GRAY, bold=True, sub="existing")
    box(ax, 36, 30, 29, 14, "Assistant API", BLUE, bold=True, sub="Cloud Run · Gemini on Vertex AI")
    arrow(ax, (29, 37), (36, 37))
    arrow(ax, (65, 37), (72, 37))
    note(ax, 68.5, 47, "retrieve\n+ tools", fs=9, ha="center")
    # tools & guard
    box(ax, 36, 8, 29, 14, "SQL guard", RED, bold=True, sub="parse · read-only · schema check\nEXPLAIN on replica")
    arrow(ax, (50.5, 30), (50.5, 22), RED[1])
    box(ax, 72, 8, 45, 14, "Eval after every sync", AMBER, bold=True,
        sub="golden questions · keep old index if it drops")
    arrow(ax, (94.5, 30), (94.5, 22), AMBER[1])
    note(ax, 3, 2, "Read-only everywhere. Schema and reference data only, no customer rows.", fs=10,
         style="italic")
    save(f, "03-architecture.png")


# 4. Sync triggers -----------------------------------------------------------------
def d04():
    f, ax = fig(66, "Decision 2: sync on change, reconcile on schedule")
    rows = [("Bitbucket", "prod tag moved", "webhook · HMAC verified", "changed files"),
            ("Confluence", "page edited", "CQL poll every 15 min", "changed pages"),
            ("Schema", "migration deployed", "read replica catalog", "changed tables")]
    for i, (src, ev, how, what) in enumerate(rows):
        y = 44 - i * 13
        box(ax, 3, y, 20, 9, src, GRAY, bold=True)
        box(ax, 29, y, 24, 9, ev, BLUE, sub=how, fs=10.5)
        box(ax, 59, y, 22, 9, "Re-index", BLUE, bold=True, sub=what, fs=10.5)
        arrow(ax, (23, y + 4.5), (29, y + 4.5))
        arrow(ax, (53, y + 4.5), (59, y + 4.5))
        arrow(ax, (81, y + 4.5), (88, 31), BLUE[1])
    box(ax, 88, 24, 29, 14, "Index", TEAL, bold=True, sub="each chunk versioned:\ncommit · page v · snapshot")
    box(ax, 29, 2, 52, 8, "Nightly reconcile: list everything, compare, fix drift", PURPLE, fs=10.5)
    arrow(ax, (81, 6), (102, 24), PURPLE[1], ls="--")
    for i, t in enumerate(["Idempotent: skip unchanged (hash)", "Deletes are real", "Every chunk versioned"]):
        note(ax, 88, 52 - i * 4, "✓  " + t if False else "•  " + t, fs=10, color=INK)
    note(ax, 88, 56, "RULES", fs=10, weight="bold", color=MUTED)
    save(f, "04-sync.png")


# 5. Precedence -------------------------------------------------------------------
def d05():
    f, ax = fig(66, "Decision 4: each source answers a different question")
    cols = [("Schema", "What exists?", "tables · columns · statuses", TEAL),
            ("Code in production", "What happens?", "rules as they run today", BLUE),
            ("Confluence", "What was intended?", "specs from the business team", PURPLE)]
    for i, (t, q, s, pal) in enumerate(cols):
        x = 3 + i * 39
        box(ax, x, 38, 36, 14, t, pal, bold=True, sub=q + "\n" + s, fs=12)
    # conflict example
    box(ax, 3, 4, 114, 26, "", GRAY)
    note(ax, 6, 26, "EXAMPLE ANSWER WHEN THEY DISAGREE", fs=10, weight="bold")
    note(ax, 6, 20.5, "“The CLM-482 spec says partial approvals need a second reviewer (Confluence: Partial approval, v14).",
         fs=10.5, color=INK)
    note(ax, 6, 16.5, "The code does not check for one (approval.service.js · approvePartial @ a1b2c3d).",
         fs=10.5, color=INK)
    note(ax, 6, 12.5, "These disagree. Ask the CLM-482 owner which is correct.”", fs=10.5, color=INK)
    box(ax, 6, 5.5, 34, 4.5, "Both cited · conflict flagged", ("#ffffff", AMBER[1]), fs=9.5, lw=1.2)
    save(f, "05-precedence.png")


# 6. SQL guard -------------------------------------------------------------------
def d06():
    f, ax = fig(64, "Decision 5: check SQL against today's schema; never run it")
    steps = [("Draft SQL", "model + catalog tools", BLUE),
             ("Parse", "one statement", GRAY),
             ("Read-only", "no writes anywhere", GRAY),
             ("Schema check", "tables + columns\nexist today", GRAY),
             ("EXPLAIN", "read replica ·\ntimeout · read-only", GRAY)]
    w, gap = 19.5, 4
    for i, (t, s, pal) in enumerate(steps):
        x = 3 + i * (w + gap)
        box(ax, x, 30, w, 14, t, pal, bold=True, sub=s, fs=11)
        if i < len(steps) - 1:
            arrow(ax, (x + w, 37), (x + w + gap, 37))
    # fail loop
    ax.annotate("", xy=(12.75, 44), xytext=(73, 44),
                arrowprops=dict(arrowstyle="-|>", color=RED[1], lw=1.6, ls="--",
                                connectionstyle="arc3,rad=0.18", mutation_scale=14))
    note(ax, 43, 53.5, "fails → error back to the model, retry (limited)", fs=10, ha="center", color=RED[1])
    box(ax, 74, 6, 43, 14, "Shown to a person", GREEN, bold=True, sub="with tables and columns linked\nperson runs it on the replica")
    arrow(ax, (107, 30), (100, 20), GREEN[1])
    box(ax, 3, 6, 58, 14, "Never", RED, bold=True, sub="executed automatically · run on primary · given write access")
    save(f, "06-sql-guard.png")


# 7. Answer card ------------------------------------------------------------------
def d07():
    f, ax = fig(66, "Decision 6: every answer says where it came from, and how fresh")
    ax.add_patch(FancyBboxPatch((10, 1), 100, 54, boxstyle="round,pad=0,rounding_size=2", fc="#ffffff",
                                ec=GRAY[1], lw=1.6))
    box(ax, 56, 46, 50, 6, "SQL for claims stuck in review over 48h?", BLUE, fs=10.5)
    note(ax, 14, 41, "Claims waiting on review are in UNDER_REVIEW or, since CLM-482,", fs=10.5, color=INK)
    note(ax, 14, 37.5, "PARTIALLY_APPROVED. Status changes are in claim_status_history.", fs=10.5, color=INK)
    ax.add_patch(FancyBboxPatch((14, 22), 92, 11, boxstyle="round,pad=0,rounding_size=1", fc="#f6f8fa",
                                ec=GRAY[1], lw=1))
    for i, line in enumerate(["SELECT c.claim_id, c.status, h.changed_at",
                              "FROM claims c JOIN claim_status_history h ON …",
                              "WHERE c.status IN ('UNDER_REVIEW','PARTIALLY_APPROVED') …"]):
        ax.text(16, 30.5 - i * 3.3, line, fontsize=9.5, family="DejaVu Sans Mono", color=INK, va="center")
    box(ax, 80, 23, 24, 3.6, "✓ guard passed", ("#ffffff", GREEN[1]), fs=9, lw=1.1)
    ax.plot([14, 106], [19, 19], color=GRAY[1], lw=1)
    note(ax, 14, 16, "SOURCES", fs=9, weight="bold")
    srcs = [("Schema · claims, claim_status_history", "snapshot today 09:10", TEAL),
            ("Confluence · CLM / Partial approval", "v14 · edited 2 h ago", PURPLE),
            ("Code · src/domain/claimStatus.js", "prod @ a1b2c3d", BLUE)]
    for i, (s, v, pal) in enumerate(srcs):
        yy = 12 - i * 3.3
        ax.add_patch(FancyBboxPatch((14, yy - 1.1), 1.6, 2.2, boxstyle="round,pad=0,rounding_size=0.5",
                                    fc=pal[1], ec="none"))
        note(ax, 17.5, yy, s, fs=9.5, color=INK)
        note(ax, 104, yy, v, fs=9.5, ha="right")
    save(f, "07-answer-card.png")


# 8. Rollout -------------------------------------------------------------------
def d08():
    f, ax = fig(46, "Rollout: prevent wrong SQL first, retire the old context last")
    phases = [("1. Schema + SQL guard", "catalog, join paths,\nstatus values, guard", TEAL),
              ("2. Confluence", "section chunks,\n15-min sync", PURPLE),
              ("3. Code", "function, class, route\nchunks on deploy", BLUE),
              ("4. Compare, switch", "golden questions:\nold vs new", GREEN)]
    w = 25.5
    for i, (t, s, pal) in enumerate(phases):
        x = 3 + i * (w + 4)
        box(ax, x, 10, w, 20, "", pal)
        note(ax, x + w / 2, 25.5, t, fs=11, weight="bold", color=INK, ha="center")
        note(ax, x + w / 2, 16.5, s, fs=10, ha="center")
        if i < 3:
            arrow(ax, (x + w, 20), (x + w + 4, 20), PURPLE[1], lw=2.2)
    note(ax, 3, 4, "The hand-built context stays until the new system wins on citations and SQL validity.",
         fs=10, style="italic")
    save(f, "08-rollout.png")


if __name__ == "__main__":
    for fn in (d01, d02, d03, d04, d05, d06, d07, d08):
        fn()
    print(sorted(os.listdir(OUT)))
