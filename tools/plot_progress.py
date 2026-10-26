"""Plot how many ducks finish the real course at each saved checkpoint of one or more training runs.

Reads the JSON reports written by ``training/runs/phase6-course/eval_checkpoints.sh`` (one folder per run, files
``model_<iteration>.json``). Two panels, same x-axis: finished (%) and measured walking speed (m/s). A dashed grey
line marks a reference report (e.g. NVIDIA's checkpoint before training). Run from isaac-obstacle-course/:

    uv run --no-project --with matplotlib python tools/plot_progress.py OUT.png \\
        "Run B (progress reward)":training/runs/phase6-course/progress/course_finetune_v2_progress \\
        "Run A (NVIDIA's rewards only)":training/runs/phase6-course/progress/course_finetune_from_nvidia \\
        --reference "NVIDIA, before":training/runs/phase5-before/eval/before_nvidia.json
"""

import argparse
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]  # categorical slots 1-4 (dataviz reference palette)
INK, MUTED, GRID, REF = "#0b0b0b", "#52514e", "#e4e2dc", "#8a8780"


def load_run(folder: Path) -> list[tuple[int, float, float]]:
    rows = []
    for f in folder.glob("model_*.json"):
        s = json.loads(f.read_text())["summary"]
        rows.append((int(re.search(r"model_(\d+)", f.name).group(1)), s["finished_pct"], s["mean_vx"]))
    return sorted(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("runs", nargs="+", help='"label":folder')
    ap.add_argument("--reference", help='"label":report.json')
    ap.add_argument("--xlabel", default="training iteration (NVIDIA's checkpoint = 49,999)")
    a = ap.parse_args()
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    for i, spec in enumerate(a.runs):
        label, folder = spec.split(":", 1)
        rows = load_run(Path(folder))
        x = [r[0] for r in rows]
        for ax, k in ((top, 1), (bottom, 2)):
            y = [r[k] for r in rows]
            ax.plot(x, y, color=SERIES[i], linewidth=2, marker="o", markersize=5, label=label)
            ax.annotate(f"{y[-1]:.0f} %" if k == 1 else f"{y[-1]:.2f}", (x[-1], y[-1]), textcoords="offset points",
                        xytext=(7, 6 - 12 * i), fontsize=9, color=INK)
    if a.reference:
        label, path = a.reference.split(":", 1)
        s = json.loads(Path(path).read_text())["summary"]
        for ax, v in ((top, s["finished_pct"]), (bottom, s["mean_vx"])):
            ax.axhline(v, color=REF, linestyle="--", linewidth=1.5, label=label)
    top.set_ylabel("ducks that finish [%]", color=MUTED)
    bottom.set_ylabel("walking speed [m/s]\n(asked: 0.24)", color=MUTED)
    bottom.set_xlabel(a.xlabel, color=MUTED)
    top.set_ylim(0, 100)
    bottom.set_ylim(0, 0.3)
    for ax in (top, bottom):
        ax.grid(True, color=GRID, linewidth=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9)
    top.legend(frameon=False, fontsize=9, loc="lower right")
    top.set_title("Real course, 128 ducks per checkpoint, 0.25 m/s, 40 s", loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=130, facecolor="white")
    print(a.out)


if __name__ == "__main__":
    main()
