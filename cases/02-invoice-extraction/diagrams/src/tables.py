"""Table images for Post 2 (Medium has no tables). Same style as draw.py."""
import os, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from draw import INK, MUTED, BG, GRAY, BLUE, GREEN, AMBER, RED, PURPLE, OUT

FS = 12.5
LINE_H = 2.9      # data units per text line
PAD = 1.6
W = 120


def chip(ax, x, y, text, pal):
    w = len(text) * 1.15 + 3.5
    ax.add_patch(FancyBboxPatch((x, y - 1.6), w, 3.2, boxstyle="round,pad=0,rounding_size=1.5",
                                fc=pal[0], ec=pal[1], lw=1.2))
    ax.text(x + w / 2, y, text, ha="center", va="center", fontsize=FS - 1.5, color=pal[1], fontweight="bold")


def table(name, title, headers, rows, widths, chips=None, note=None, accent=BLUE):
    """widths: list of (fraction_of_W, wrap_chars). chips: {col_index: fn(text)->pal or None}."""
    chips = chips or {}
    cw = [int(fr * (W - 4) / (1.38 if i == 0 else 1.22)) for i, (fr, _) in enumerate(widths)]
    wrapped = [[textwrap.wrap(str(c), cw[i]) or [""] for i, c in enumerate(r)] for r in rows]
    heights = [max(len(c) for c in r) * LINE_H + 2 * PAD for r in wrapped]
    head_h = LINE_H + 2 * PAD
    title_h = 9
    note_h = 5 if note else 1
    H = title_h + head_h + sum(heights) + note_h
    f, ax = plt.subplots(figsize=(12, 12 * H / W), dpi=160)
    f.patch.set_facecolor(BG)
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
    ax.text(2, H - 2.5, title, fontsize=15, fontweight="bold", color=INK, va="top")

    xs, acc = [], 2
    for frac, _ in widths:
        xs.append(acc); acc += frac * (W - 4)
    y = H - title_h
    ax.add_patch(Rectangle((2, y - head_h), W - 4, head_h, fc=accent[0], ec="none"))
    ax.plot([2, W - 2], [y - head_h] * 2, color=accent[1], lw=1.6)
    for i, h in enumerate(headers):
        ax.text(xs[i] + 1.5, y - head_h / 2, h.upper(), fontsize=FS - 2.5, fontweight="bold",
                color=accent[1], va="center")
    y -= head_h
    for r, (raw, cells) in enumerate(zip(rows, wrapped)):
        h = heights[r]
        if r % 2 == 1:
            ax.add_patch(Rectangle((2, y - h), W - 4, h, fc="#fafafa", ec="none"))
        for i, lines in enumerate(cells):
            if i in chips and chips[i](raw[i]):
                chip(ax, xs[i] + 1.5, y - PAD - LINE_H / 2, raw[i], chips[i](raw[i]))
                continue
            for k, line in enumerate(lines):
                ax.text(xs[i] + 1.5, y - PAD - LINE_H * (k + 0.5), line, fontsize=FS,
                        fontweight="bold" if i == 0 else "normal", color=INK, va="center")
        y -= h
        ax.plot([2, W - 2], [y, y], color="#e5e7eb", lw=1)
    if note:
        ax.text(2, y - 3, note, fontsize=FS - 2.5, color=MUTED, style="italic", va="center")
    f.savefig(os.path.join(OUT, name), facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(f)


def t1():
    table("t1-extractor-options.png", "Two ways to extract invoices on AWS",
          ["Option", "Strengths", "Trade-offs"],
          [["Textract AnalyzeExpense",
            "Mature; standard field names such as TOTAL and VENDOR_NAME, line items, bounding boxes and per-field confidence",
            "Fixed schema; custom fields such as PO number formats or payment terms need extra mapping"],
           ["Bedrock Data Automation (BDA) with a custom blueprint",
            "You define the fields and output shape; supports custom fields and validation rules in the blueprint",
            "Newer; output can vary slightly between documents, so downstream validation is still required"]],
          [(0.24, 22), (0.40, 40), (0.36, 36)])


def t2():
    pal = lambda t: RED if t.startswith("Hard") else AMBER
    table("t2-checks.png", "The checks every invoice runs",
          ["Check", "Rule", "On failure"],
          [["Arithmetic", "Line items sum to subtotal; subtotal + tax = total (±0.01 per line for rounding)", "Review"],
           ["Vendor match", "Vendor found in vendor master by tax ID, not by name", "Review"],
           ["PO match", "PO exists, is open, and invoice amount is within tolerance (e.g. 2%) of the remaining PO value", "Review"],
           ["Duplicate", "Same vendor + invoice number, or same vendor + amount within 30 days", "Hard stop"],
           ["Bank details", "Bank account on invoice equals the one in vendor master", "Hard stop"],
           ["Field confidence", "Each field above its own threshold (see Decision 3)", "Review (field)"],
           ["Format", "Dates parse and are not in the future; currency matches the vendor's", "Review"]],
          [(0.20, 18), (0.58, 58), (0.22, 20)], chips={2: pal},
          note="No check uses a model. Hard stops go to a separate queue with its own role.")


def t3():
    pal = lambda t: RED if t.startswith("High") else AMBER if t.startswith("Medium") else GREEN
    table("t3-thresholds.png", "Thresholds per field, set by the cost of being wrong",
          ["Field", "Cost if wrong", "Threshold"],
          [["Total, tax, line amounts", "Wrong payment", "High · 98"],
           ["Invoice number", "Duplicate check fails", "High · 97"],
           ["PO number", "Wrong cost center", "Medium · 95"],
           ["Invoice date, due date", "Late fee or early payment", "Medium · 90"],
           ["Vendor address, descriptions", "Cosmetic", "Low · 80"]],
          [(0.38, 34), (0.38, 34), (0.24, 20)], chips={2: pal},
          note="Starting values, tuned on the golden set.")


def t4():
    table("t4-metrics.png", "Four numbers to watch",
          ["Metric", "Definition", "Why"],
          [["Straight-through rate", "% of invoices auto-approved", "The business value"],
           ["Escaped error rate", "% of auto-approved invoices with any wrong field, from a random 2% audit sample", "The real risk"],
           ["Field accuracy", "Per field, extracted value vs corrected value", "Where to tune thresholds"],
           ["Review time", "Median seconds per reviewed invoice", "Whether the UI works"]],
          [(0.26, 24), (0.48, 46), (0.26, 24)], accent=PURPLE)


if __name__ == "__main__":
    for fn in (t1, t2, t3, t4):
        fn()
    print("ok")
