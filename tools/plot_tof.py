"""Draw the duck's 8 x 8 ToF readings (as printed by ``PRINT_TOF=1 eval_course.py``) as distance maps.

Reads the ``[tof] duck 0 at x=... m`` blocks from a log and draws the chosen ones side by side: one hue, light = far,
dark = near, with the distance written in each zone. Run from isaac-obstacle-course/:

    uv run --no-project --with matplotlib python tools/plot_tof.py cloud/nebius/as-run/2026-10-26-depth-tof-check.log \\
        steps/media/06b/tof-maps.png --pick 0.40 4.04 --title "Flat floor ahead" "Box ahead"
"""

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

BLUES = LinearSegmentedColormap.from_list("near_dark", ["#0d3a73", "#2a78d6", "#cfe3fa"])  # near -> far
INK = "#0b0b0b"


def read(log: Path) -> dict[str, np.ndarray]:
    text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text())
    out = {}
    for m in re.finditer(r"\[tof\] duck 0 at x=([\d.]+) m.*?\n((?:[\d. ]+\n){8})", text):
        out[m.group(1)] = np.array([[float(v) for v in row.split()] for row in m.group(2).strip().splitlines()])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--pick", nargs="+", required=True, help="x positions to draw (as printed)")
    ap.add_argument("--title", nargs="+", default=None)
    a = ap.parse_args()
    grids = read(a.log)
    fig, axes = plt.subplots(1, len(a.pick), figsize=(4.2 * len(a.pick), 4.4))
    for i, (ax, x) in enumerate(zip(np.atleast_1d(axes), a.pick)):
        g = grids[x]
        ax.imshow(g, cmap=BLUES, vmin=0.3, vmax=2.0)
        for r in range(8):
            for c in range(8):
                ax.text(c, r, f"{g[r, c]:.2f}", ha="center", va="center", fontsize=7.5,
                        color="white" if g[r, c] < 1.0 else INK)
        title = a.title[i] if a.title and i < len(a.title) else f"x = {x} m"
        ax.set_title(f"{title}\n(duck at x = {x} m)", fontsize=10, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        for side in ax.spines.values():
            side.set_visible(False)
    fig.text(0.5, 0.02, "8 × 8 zones as the sensor reports them, top row first · distance in metres · darker = nearer",
             ha="center", fontsize=9, color="#52514e")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=130, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    print(a.out)


if __name__ == "__main__":
    main()
