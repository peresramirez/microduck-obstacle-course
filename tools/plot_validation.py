"""Grouped bar chart of the phase 7 validation: share of ducks that finish, per test, per policy.

Reads ``<root>/<policy>/<test>.json`` written by ``training/runs/phase7-validate/run_validate.sh`` and prints the
same numbers as a table. Run from isaac-obstacle-course/:

    uv run --no-project --with matplotlib python tools/plot_validation.py training/runs/phase7-validate/eval OUT.png \\
        --policy "nvidia:NVIDIA's checkpoint" --policy "runB:Trained on our course (blind)" [--policy "depth:...+ eyes"]
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SERIES = ["#8a8780", "#2a78d6", "#1baf7a"]  # grey = before; then categorical slots 1 and 3 of the reference palette
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e2dc"
TESTS = [
    ("real", "Real course\n0.25 m/s"),
    ("fast", "Faster\n0.35 m/s"),
    ("harder", "Harder: heights ×1.4,\nwet floor μ 0.2"),
    ("flat", "Flat lanes\n(forgetting check)"),
    ("straight", "Straight at the box\n(no steering round it)"),
    ("moved_box", "Box moved 40 cm earlier\n(never seen there)"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--policy", action="append", required=True, help="folder:label")
    a = ap.parse_args()
    policies = [p.split(":", 1) for p in a.policy]
    values = np.full((len(policies), len(TESTS)), np.nan)
    print("| Test | " + " | ".join(label for _, label in policies) + " |")
    print("|---|" + "---|" * len(policies))
    for j, (test, label) in enumerate(TESTS):
        cells = []
        for i, (folder, _) in enumerate(policies):
            f = a.root / folder / f"{test}.json"
            if f.exists():
                s = json.loads(f.read_text())["summary"]
                values[i, j] = s["finished_pct"]
                cells.append(f"{s['finished']}/{s['ducks']} ({s['finished_pct']:.0f} %), fell {s['fell']}")
            else:
                cells.append("—")
        print(f"| {label.replace(chr(10), ' ')} | " + " | ".join(cells) + " |")
    fig, ax = plt.subplots(figsize=(10, 4.6))
    width = 0.8 / len(policies)
    x = np.arange(len(TESTS))
    for i, (_, label) in enumerate(policies):
        pos = x - 0.4 + width * (i + 0.5)
        bars = ax.bar(pos, np.nan_to_num(values[i]), width - 0.03, color=SERIES[i], label=label)
        for b, v in zip(bars, values[i]):
            if not np.isnan(v):
                ax.annotate(f"{v:.0f}", (b.get_x() + b.get_width() / 2, v), textcoords="offset points",
                            xytext=(0, 3), ha="center", fontsize=8, color=INK)
    ax.set_xticks(x, [label for _, label in TESTS], fontsize=9, color=MUTED)
    ax.set_ylabel("ducks that finish [%]", color=MUTED)
    ax.set_ylim(0, 108)
    ax.grid(True, axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=len(policies))
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=130, facecolor="white")
    print(a.out)


if __name__ == "__main__":
    main()
