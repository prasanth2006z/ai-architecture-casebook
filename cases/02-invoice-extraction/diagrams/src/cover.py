"""Story preview (cover) image for Post 2, matching the Case 01 cover style:
dark navy grid, spaced eyebrow, large white title, small flow on the right. 1600x900."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from draw import OUT

NAVY_TOP, NAVY_BOT = "#0b1733", "#14295a"
GRID = "#ffffff"
EYEBROW = "#8fb0ff"
WHITE = "#ffffff"
SOFT = "#c7d4f2"
LINE = "#5b7fd6"
BRIGHT = "#7aa2ff"
BOX_FC = "#0f1f45"
GREEN, AMBER, RED = "#4ade80", "#fbbf24", "#f87171"

W, H = 160, 90
f = plt.figure(figsize=(16, 9), dpi=100)
ax = f.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(5, H + 5); ax.axis("off")

# background gradient + faint grid
grad = np.linspace(0, 1, 256).reshape(-1, 1)
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("bg", [NAVY_BOT, NAVY_TOP])
ax.imshow(grad, extent=[0, W, -10, H + 15], cmap=cmap, aspect="auto", zorder=0)
for x in np.arange(0, W + 1, 5):
    ax.plot([x, x], [-10, H + 15], color=GRID, alpha=0.04, lw=1, zorder=1)
for y in np.arange(-10, H + 16, 5):
    ax.plot([0, W], [y, y], color=GRID, alpha=0.04, lw=1, zorder=1)


def spaced(s):
    return " ".join(s).replace("   ", " ")


# left: eyebrow, title, subline
ax.text(12, 72, spaced("AI ARCHITECTURE CASEBOOK · CASE 02"), fontsize=19, color=EYEBROW,
        fontweight="bold", va="center", zorder=3)
for i, line in enumerate(["Invoice Extraction", "with Human Review"]):
    ax.text(12, 60 - i * 10, line, fontsize=50, color=WHITE, fontweight="bold", va="center", zorder=3)
ax.text(12, 38, "Route on checks, not on confidence.", fontsize=22, color=SOFT, va="center", zorder=3)


def box(x, y, w, h, title, sub=None, ec=LINE, lw=1.8, tc=WHITE, fs=15, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=BOX_FC, ec=ec, lw=lw, zorder=3))
    cy = y + h / 2
    if sub:
        ax.text(x + w / 2, cy + 1.8, title, ha="center", va="center", fontsize=fs, color=tc,
                fontweight="bold" if bold else "normal", zorder=4)
        ax.text(x + w / 2, cy - 2.2, sub, ha="center", va="center", fontsize=12.5, color=SOFT, zorder=4)
    else:
        ax.text(x + w / 2, cy, title, ha="center", va="center", fontsize=fs, color=tc,
                fontweight="bold" if bold else "normal", zorder=4)


def arrow(p1, p2, color=BRIGHT, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=18, color=color, lw=2,
                                 linestyle=ls, shrinkA=0, shrinkB=1, zorder=2))


# right: flow
cx = 124
box(100, 66, 48, 9, "TOTAL $12,480.00 · 99.9%", fs=15)
arrow((cx, 66), (cx, 58))
box(104, 45, 40, 13, "Deterministic checks", "duplicate · bank · PO · math", ec=BRIGHT, lw=2.6, bold=True, fs=17)
for tx, col in [(110, GREEN), (cx, AMBER), (138, RED)]:
    arrow((cx, 45), (tx, 33), color=col)
box(98, 24, 18, 9, "Auto-approve", ec=GREEN, fs=12.5)
box(117, 24, 14, 9, "Review", ec=AMBER, fs=12.5)
box(132, 24, 16, 9, "Hard stop", ec=RED, fs=12.5)
f.savefig(os.path.join(OUT, "00-cover.png"))
plt.close(f)
print("ok")
