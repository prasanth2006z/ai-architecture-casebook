"""Diagrams for Post 2: Invoice extraction with human review.
Run: python3 draw.py  -> writes PNGs into ./img
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
from matplotlib import font_manager

for f in font_manager.findSystemFonts():
    if "Inter" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Inter"

OUT = os.path.join(os.path.dirname(__file__), "img")
os.makedirs(OUT, exist_ok=True)

INK = "#1f2937"
MUTED = "#6b7280"
LINE = "#9ca3af"
BG = "#ffffff"
GRAY = ("#f3f4f6", "#d1d5db")
BLUE = ("#eff6ff", "#2563eb")
GREEN = ("#ecfdf5", "#059669")
AMBER = ("#fffbeb", "#d97706")
RED = ("#fef2f2", "#dc2626")
PURPLE = ("#f5f3ff", "#7c3aed")

W = 120  # data units across


def fig(h, title=None):
    f, ax = plt.subplots(figsize=(12, 12 * h / W), dpi=160)
    f.patch.set_facecolor(BG)
    ax.set_xlim(0, W)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.text(3, h - 4, title, fontsize=15, fontweight="bold", color=INK, va="top")
    return f, ax


def box(ax, x, y, w, h, text, pal=GRAY, fs=11, bold=False, sub=None, tc=INK, lw=1.6, align="center"):
    fc, ec = pal
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.4",
                                fc=fc, ec=ec, lw=lw))
    cx = x + w / 2 if align == "center" else x + 2
    ha = "center" if align == "center" else "left"
    if sub:
        ax.text(cx, y + h * 0.62, text, ha=ha, va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=tc)
        ax.text(cx, y + h * 0.28, sub, ha=ha, va="center", fontsize=fs - 2.2, color=MUTED,
                linespacing=1.3)
    else:
        ax.text(cx, y + h / 2, text, ha=ha, va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", color=tc, linespacing=1.35)


def arrow(ax, p1, p2, color=LINE, label=None, lw=1.8, ls="-", rad=0.0, lpos=0.5, loff=(0, 1.6), lc=MUTED, fs=9.5):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=15, color=color, lw=lw,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))
    if label:
        lx = p1[0] + (p2[0] - p1[0]) * lpos + loff[0]
        ly = p1[1] + (p2[1] - p1[1]) * lpos + loff[1]
        ax.text(lx, ly, label, ha="center", va="center", fontsize=fs, color=lc,
                bbox=dict(fc=BG, ec="none", pad=1.2))


def note(ax, x, y, text, fs=10, color=MUTED, ha="left", style="normal", weight="normal"):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va="center", style=style,
            fontweight=weight, linespacing=1.4)


def save(f, name):
    f.savefig(os.path.join(OUT, name), facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(f)


# 1. The problem ---------------------------------------------------------------
def d01():
    f, ax = fig(52, "Today vs. the goal")
    note(ax, 3, 41, "TODAY", fs=10, weight="bold", color=MUTED)
    box(ax, 3, 30, 26, 8, "6,000 invoices / month", GRAY, sub="PDFs · scans · phone photos")
    box(ax, 41, 30, 30, 8, "3 clerks re-key every field", AMBER, sub="vendor · lines · tax · total · PO")
    box(ax, 83, 30, 18, 8, "ERP", GRAY, bold=True)
    arrow(ax, (29, 34), (41, 34))
    arrow(ax, (71, 34), (83, 34))

    note(ax, 3, 23, "GOAL", fs=10, weight="bold", color=BLUE[1])
    box(ax, 3, 9, 20, 9, "Invoices", GRAY)
    box(ax, 33, 9, 20, 9, "AI extracts", BLUE, bold=True)
    box(ax, 66, 14.5, 30, 7, "Clean → ERP automatically", GREEN)
    box(ax, 66, 3.5, 30, 7, "Unsure → person checks", AMBER)
    arrow(ax, (23, 13.5), (33, 13.5))
    arrow(ax, (53, 15), (66, 18))
    arrow(ax, (53, 12), (66, 7))
    ax.text(108, 12.5, "How does the\nsystem know it\nis unsure?", ha="center", va="center", fontsize=11,
            fontweight="bold", color=RED[1], linespacing=1.35)
    save(f, "01-problem.png")


# 2. Confidence vs correctness ---------------------------------------------------
def d02():
    f, ax = fig(58, "High confidence, wrong outcome")
    # invoice card
    box(ax, 3, 6, 40, 40, "", GRAY)
    note(ax, 7, 42, "INVOICE  INV-4471", fs=10.5, weight="bold", color=INK)
    note(ax, 7, 38, "Acme Supplies Ltd", fs=10, color=MUTED)
    for i, (k, v) in enumerate([("Line items", "3"), ("Tax", "$1,248.00"), ("Bank", "NEW ACCOUNT")]):
        note(ax, 7, 31 - i * 4.5, k, fs=10, color=MUTED)
        note(ax, 39, 31 - i * 4.5, v, fs=10, color=INK, ha="right")
    ax.add_patch(FancyBboxPatch((6, 9), 34, 7, boxstyle="round,pad=0,rounding_size=1", fc=BLUE[0], ec=BLUE[1], lw=1.6))
    note(ax, 8, 12.5, "TOTAL  $12,480.00", fs=11, weight="bold", color=INK)
    note(ax, 38, 12.5, "99.9%", fs=11, weight="bold", color=BLUE[1], ha="right")

    # what confidence tells you
    box(ax, 52, 34, 30, 12, "What confidence tells you", BLUE, bold=True, fs=11,
        sub="“I read these characters correctly.”")
    arrow(ax, (40, 12.5), (52, 38), BLUE[1], rad=-0.2)
    # what finance needs
    box(ax, 87, 34, 30, 12, "What finance needs to know", RED, bold=True, fs=11,
        sub="“Should we pay this?”")
    items = [("Duplicate of an invoice paid on 3 Oct", RED),
             ("No open purchase order", AMBER),
             ("Bank account differs from vendor master", RED)]
    for i, (t, pal) in enumerate(items):
        y = 23 - i * 8
        box(ax, 52, y, 65, 6, "×  " + t, pal, fs=10.5, align="left")
    note(ax, 52, 2, "Every value was read correctly. None of these invoices should be paid.", fs=10,
         style="italic")
    save(f, "02-confidence-vs-correctness.png")


# 3. Architecture ---------------------------------------------------------------
def d03():
    f, ax = fig(78, "The design in one picture")
    box(ax, 3, 60, 18, 8, "Upload", GRAY, sub="email · portal · scan")
    box(ax, 26, 60, 14, 8, "S3 raw/", GRAY, bold=True)
    box(ax, 45, 60, 18, 8, "EventBridge", GRAY, bold=True)
    arrow(ax, (21, 64), (26, 64))
    arrow(ax, (40, 64), (45, 64))
    # step functions container
    ax.add_patch(FancyBboxPatch((3, 33), 114, 20, boxstyle="round,pad=0,rounding_size=1.6",
                                fc="#fafafa", ec=PURPLE[1], lw=1.4, ls="--"))
    note(ax, 114, 50.5, "Step Functions workflow", fs=10, weight="bold", color=PURPLE[1], ha="right")
    box(ax, 8, 36, 30, 11, "1. Extract", BLUE, bold=True, sub="Textract or BDA")
    box(ax, 45, 36, 30, 11, "2. Validate", BLUE, bold=True, sub="deterministic checks")
    box(ax, 82, 36, 30, 11, "3. Route", BLUE, bold=True, sub="tiered decision")
    arrow(ax, (54, 60), (23, 47.5), rad=0.15)
    arrow(ax, (38, 41.5), (45, 41.5))
    arrow(ax, (75, 41.5), (82, 41.5))
    # outcomes
    box(ax, 3, 15, 28, 10, "Auto-approve", GREEN, bold=True, sub="post to ERP")
    box(ax, 45, 15, 30, 10, "Human review", AMBER, bold=True, sub="only flagged fields")
    box(ax, 84, 15, 30, 10, "Hard stop", RED, bold=True, sub="fraud · duplicate")
    arrow(ax, (88, 36), (17, 25), GREEN[1])
    arrow(ax, (95, 36), (60, 25), AMBER[1])
    arrow(ax, (102, 36), (99, 25), RED[1])
    # audit + corrections
    arrow(ax, (31, 18), (45, 18), AMBER[1], ls="--")
    note(ax, 38, 11.5, "2% random\naudit", fs=9, ha="center", color=AMBER[1])
    box(ax, 45, 1.5, 30, 8, "Corrections store", PURPLE, bold=True, sub="golden set · metrics")
    arrow(ax, (60, 15), (60, 9.5), PURPLE[1])
    save(f, "03-architecture.png")


# 4. Extractor is replaceable ---------------------------------------------------
def d04():
    f, ax = fig(50, "Decision 1: swap the extractor, keep the rules")
    box(ax, 3, 26, 30, 10, "Textract AnalyzeExpense", BLUE, bold=True, sub="standard fields · per-field confidence")
    box(ax, 3, 10, 30, 10, "Bedrock Data Automation", BLUE, bold=True, sub="custom blueprint · your schema")
    box(ax, 44, 14, 28, 18, "Adapter", GRAY, bold=True,
        sub="one normalized Invoice:\nfields · values ·\nconfidence · page geometry")
    box(ax, 84, 14, 33, 18, "Checks · Routing · Review", GREEN, bold=True,
        sub="your business rules\nstays fixed")
    arrow(ax, (33, 31), (44, 26))
    arrow(ax, (33, 15), (44, 20), ls="--")
    arrow(ax, (72, 23), (84, 23))
    note(ax, 18, 39, "SWAPPABLE", fs=10, weight="bold", color=BLUE[1], ha="center")
    note(ax, 100.5, 35, "THE PRODUCT", fs=10, weight="bold", color=GREEN[1], ha="center")
    note(ax, 3, 4, "Pick the extractor with the best score on your golden set. Nothing downstream changes.",
         fs=10, style="italic")
    save(f, "04-extractor-replaceable.png")


# 5. Deterministic checks ------------------------------------------------------
def d05():
    f, ax = fig(70, "Decision 2: every invoice runs the same checks (no model involved)")
    box(ax, 3, 27, 18, 12, "Extracted\ninvoice", GRAY, bold=True)
    # hard stop group
    ax.add_patch(FancyBboxPatch((30, 47), 50, 13, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=RED[0], ec=RED[1], lw=1.2, ls="--"))
    note(ax, 33, 57.5, "If failed → HARD STOP", fs=10, weight="bold", color=RED[1])
    box(ax, 33, 49, 21, 6, "Duplicate", BG and ("#ffffff", RED[1]), fs=10)
    box(ax, 56, 49, 21, 6, "Bank details", ("#ffffff", RED[1]), fs=10)
    # review group
    ax.add_patch(FancyBboxPatch((30, 9), 50, 34, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=AMBER[0], ec=AMBER[1], lw=1.2, ls="--"))
    note(ax, 33, 40.5, "If failed → REVIEW (with the reason)", fs=10, weight="bold", color=AMBER[1])
    rv = ["Arithmetic: lines = subtotal, + tax = total", "Vendor matched by tax ID", "PO open, amount within tolerance",
          "Each field above its own threshold", "Dates valid, currency matches vendor"]
    for i, t in enumerate(rv):
        box(ax, 33, 32 - i * 5.3, 44, 4.3, t, ("#ffffff", AMBER[1]), fs=9.5, align="left", lw=1.1)
    arrow(ax, (21, 35), (30, 52), rad=-0.15)
    arrow(ax, (21, 32), (30, 26))
    box(ax, 90, 27, 27, 12, "All pass", GREEN, bold=True, sub="→ continue to routing")
    arrow(ax, (80, 33), (90, 33), GREEN[1])
    note(ax, 3, 3, "Names are for display, IDs are for joins. Bank details are never updated from an invoice.",
         fs=10, style="italic")
    save(f, "05-deterministic-checks.png")


# 6. Thresholds per field ------------------------------------------------------
def d06():
    fields = ["Vendor address,\ndescriptions", "Invoice date,\ndue date", "PO number", "Invoice number",
              "Total, tax,\nline amounts"]
    vals = [80, 90, 95, 97, 98]
    cost = ["Cosmetic", "Late fee or early payment", "Wrong cost center", "Duplicate check fails", "Wrong payment"]
    cols = [GREEN[1], AMBER[1], AMBER[1], RED[1], RED[1]]
    f, ax = plt.subplots(figsize=(12, 5.6), dpi=160)
    f.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    bars = ax.barh(fields, [v - 70 for v in vals], left=70, color=cols, height=0.56)
    for b, v, c in zip(bars, vals, cost):
        ax.text(v + 0.4, b.get_y() + b.get_height() / 2, f"{v}   ·   {c}", va="center", fontsize=10.5, color=INK)
    ax.set_xlim(70, 108)
    ax.set_xticks([70, 80, 90, 100])
    ax.tick_params(colors=MUTED, labelsize=10.5, length=0)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRAY[1])
    ax.grid(axis="x", color="#eef0f3", lw=1)
    ax.set_axisbelow(True)
    ax.set_xlabel("Minimum confidence before a field can skip review", color=MUTED, fontsize=10.5)
    ax.set_title("Decision 3: thresholds per field, set by the cost of being wrong", loc="left",
                 fontsize=15, fontweight="bold", color=INK, pad=14)
    for lbl in ax.get_yticklabels():
        lbl.set_color(INK)
    f.text(0.01, -0.02, "Starting values, tuned on the golden set. Color = cost if the field is wrong.",
           fontsize=10, color=MUTED, style="italic")
    f.tight_layout()
    save(f, "06-thresholds-per-field.png")


# 7. Review loop ---------------------------------------------------------------
def d07():
    f, ax = fig(80, "Decision 4: a review loop you own")
    # left: the loop
    box(ax, 3, 56, 40, 11, "Step Functions: review step", PURPLE, bold=True, sub=".waitForTaskToken → workflow pauses")
    box(ax, 3, 38, 40, 10, "DynamoDB queue", GRAY, bold=True, sub="invoice · reasons · reviewer · SLA")
    box(ax, 3, 20, 40, 10, "Review UI (Cognito)", BLUE, bold=True, sub="confirm or correct each flagged field")
    box(ax, 3, 2, 40, 10, "SendTaskSuccess", GREEN, bold=True, sub="corrected invoice → workflow resumes → ERP")
    arrow(ax, (23, 56), (23, 48))
    arrow(ax, (23, 38), (23, 30))
    arrow(ax, (23, 20), (23, 12))
    # right: screen mock
    ax.add_patch(FancyBboxPatch((52, 8), 65, 60, boxstyle="round,pad=0,rounding_size=1.6", fc="#ffffff", ec=GRAY[1], lw=1.4))
    ax.add_patch(FancyBboxPatch((52, 63), 65, 5, boxstyle="round,pad=0,rounding_size=1.6", fc=GRAY[0], ec=GRAY[1], lw=1.4))
    note(ax, 55, 65.5, "Review · INV-4471 · 2 flagged fields", fs=9.5, weight="bold", color=INK)
    # pdf pane
    ax.add_patch(FancyBboxPatch((55, 12), 30, 48, boxstyle="round,pad=0,rounding_size=0.8", fc="#fafafa", ec=GRAY[1], lw=1))
    for i in range(9):
        ax.plot([58, 82 - (i % 3) * 4], [55 - i * 4.2] * 2, color="#e5e7eb", lw=3, solid_capstyle="round")
    ax.add_patch(FancyBboxPatch((70, 17), 13, 5, boxstyle="round,pad=0,rounding_size=0.5", fc="none", ec=AMBER[1], lw=2))
    ax.add_patch(FancyBboxPatch((57, 33.4), 22, 3.6, boxstyle="round,pad=0,rounding_size=0.5", fc="none", ec=AMBER[1], lw=2))
    note(ax, 70, 14.3, "PDF with highlights", fs=8.5, ha="center")
    # side panel
    def field(y, name, val, reason):
        box(ax, 88, y, 26, 15, "", AMBER, lw=1.2)
        note(ax, 90, y + 12, name, fs=9, weight="bold", color=INK)
        note(ax, 90, y + 8.5, val, fs=9.5, color=INK)
        note(ax, 90, y + 5, reason, fs=8, color=AMBER[1])
        box(ax, 90, y + 1, 10, 2.8, "Confirm", ("#ffffff", GREEN[1]), fs=8, lw=1)
        box(ax, 102, y + 1, 10, 2.8, "Correct", ("#ffffff", BLUE[1]), fs=8, lw=1)
    field(43, "TOTAL", "$12,480.00", "Lines sum to 11,980.00")
    field(25, "PO NUMBER", "PO-77812", "PO closed on 30 Sep")
    note(ax, 101, 14, "Only flagged fields shown.\nEach one must be touched.", fs=8.5, ha="center")
    save(f, "07-review-loop.png")


# 8. Measure what escapes --------------------------------------------------------
def d08():
    f, ax = fig(76, "Decision 5: measure what escapes, not just what gets reviewed")
    box(ax, 44, 58, 32, 8, "All invoices", GRAY, bold=True)
    box(ax, 8, 40, 36, 10, "Auto-approved", GREEN, bold=True, sub="never seen by a person…")
    box(ax, 76, 40, 36, 10, "Sent to review", AMBER, bold=True, sub="corrections are visible")
    arrow(ax, (54, 58), (30, 50))
    arrow(ax, (66, 58), (90, 50))
    box(ax, 8, 22, 36, 10, "Random 2% audit", AMBER, bold=True, sub="reviewer is not told")
    arrow(ax, (26, 40), (26, 32), AMBER[1], ls="--")
    box(ax, 8, 4, 36, 10, "Escaped error rate", RED, bold=True, sub="the only unbiased risk number")
    arrow(ax, (26, 22), (26, 14), RED[1])
    box(ax, 76, 22, 36, 10, "Corrections store", PURPLE, bold=True, sub="invoice · field · before · after · reason")
    arrow(ax, (94, 40), (94, 32), PURPLE[1])
    arrow(ax, (44, 27), (76, 27), PURPLE[1], ls="--", label="audit corrections too", loff=(0, 2.2))
    box(ax, 76, 4, 36, 10, "Feeds", ("#ffffff", PURPLE[1]), bold=True, fs=10,
        sub="golden set · vendor watch list ·\nrelease gate (Post 4)")
    arrow(ax, (94, 22), (94, 14), PURPLE[1])
    save(f, "08-measure-escapes.png")


# 9. Router --------------------------------------------------------------------
def diamond(ax, cx, cy, w, h, text, pal=GRAY):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
                         closed=True, fc=pal[0], ec=pal[1], lw=1.6))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=10, color=INK, linespacing=1.3)


def d09():
    f, ax = fig(106, "The router, in order")
    cx = 34
    qs = [(80, "Duplicate or\nbank mismatch?", ("HARD STOP", RED)),
          (60, "Any check\nfailed?", ("REVIEW", AMBER)),
          (40, "Amount over\nauto limit?", ("REVIEW", AMBER)),
          (20, "In random\naudit sample?", ("REVIEW", AMBER))]
    box(ax, cx - 9, 89, 18, 5, "Checks done", GRAY, bold=True, fs=10)
    arrow(ax, (cx, 89), (cx, 87))
    for i, (y, q, (out, pal)) in enumerate(qs):
        diamond(ax, cx, y, 30, 13, q)
        box(ax, 70, y - 4, 26, 8, out, pal, bold=True, fs=11)
        arrow(ax, (cx + 15, y), (70, y), pal[1], label="yes", loff=(0, 1.8))
        nxt = qs[i + 1][0] + 6.5 if i < 3 else 9
        arrow(ax, (cx, y - 6.5), (cx, nxt), label="no", lpos=0.45, loff=(3, 0))
    box(ax, cx - 14, 1, 28, 8, "AUTO-APPROVE", GREEN, bold=True, fs=11)
    ax.add_patch(FancyBboxPatch((70, 1), 46, 8, boxstyle="round,pad=0,rounding_size=1.4", fc="#ffffff", ec=LINE, lw=1.2, ls="--"))
    note(ax, 93, 5, "There is no “high confidence →\nskip the checks” path.", fs=9.5, ha="center", style="italic")
    save(f, "09-router.png")


# 10. Rollout ------------------------------------------------------------------
def d10():
    f, ax = fig(44, "Rollout: widen only when the audit says so")
    phases = [("Weeks 1–4: shadow mode", "everything reviewed;\nsystem's route recorded,\nnot used", GRAY),
              ("Pilot: one vendor group", "clean history, low amounts;\nauto-approve on,\naudit sample watched", BLUE),
              ("Widen, group by group", "each group under the\nescaped-error limit\nfor a full month", GREEN)]
    for i, (t, s, pal) in enumerate(phases):
        x = 3 + i * 40
        box(ax, x, 8, 33, 22, "", pal)
        note(ax, x + 16.5, 25.5, t, fs=11, weight="bold", color=INK, ha="center")
        note(ax, x + 16.5, 16, s, fs=9.5, ha="center")
        if i < 2:
            arrow(ax, (x + 33, 19), (x + 40, 19), PURPLE[1], lw=2.2)
    note(ax, 39.5, 34, "gate: golden set built", fs=9, ha="center", color=PURPLE[1])
    note(ax, 79.5, 34, "gate: audit under limit", fs=9, ha="center", color=PURPLE[1])
    note(ax, 3, 3, "Agree the escaped-error limit with finance before launch.", fs=10, style="italic")
    save(f, "10-rollout.png")


if __name__ == "__main__":
    for fn in [d01, d02, d03, d04, d05, d06, d07, d08, d09, d10]:
        fn()
    print(sorted(os.listdir(OUT)))
