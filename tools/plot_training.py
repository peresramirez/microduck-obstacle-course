"""Plot training curves from an Isaac Lab / RSL-RL run's TensorBoard events into one PNG (a small multiple per metric).

Run from isaac-obstacle-course/ on the Mac, after copying the run back (``cloud/nebius/sync.sh down``):

    uv run --no-project --with tensorboard --with matplotlib python tools/plot_training.py \\
        training/runs/phase6-course steps/media/06/training-curves.png --title "Fine-tune on our course" \\
        [--tag Train/mean_reward:"Mean reward" ...] [--clip Train/mean_reward:-50:150] [--smooth 25]

Without ``--tag`` it plots reward, episode length, the curriculum level, the fall rate and the velocity tracking
error, whichever of them the run logged. ``--list`` prints every scalar tag in the run.
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator  # noqa: E402

DEFAULT_TAGS = (
    ("Train/mean_reward", "Mean reward"),
    ("Train/mean_episode_length", "Mean episode length [steps]"),
    ("Curriculum/terrain_levels", "Curriculum: mean difficulty row (0-9)"),
    ("Episode_Termination/fell_over", "Episodes ending in a fall [share]"),
    ("Metrics/base_velocity/error_vel_xy", "Velocity tracking error [m/s]"),
)
INK, MUTED, LINE, SERIES = "#1d1d1b", "#5d5b55", "#dedbd2", "#2563eb"


def load(run: Path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    acc = EventAccumulator(str(run), size_guidance={"scalars": 0})
    acc.Reload()
    return {t: (np.array([e.step for e in acc.Scalars(t)]), np.array([e.value for e in acc.Scalars(t)]))
            for t in acc.Tags()["scalars"]}


def smooth(y: np.ndarray, k: int) -> np.ndarray:
    if k <= 1 or len(y) < k:
        return y
    pad = np.pad(y, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path, help="folder holding events.out.tfevents.*")
    ap.add_argument("out", type=Path, nargs="?")
    ap.add_argument("--title", default="")
    ap.add_argument("--tag", action="append", default=[], help="TAG[:label]")
    ap.add_argument("--clip", action="append", default=[], help="TAG:min:max (y-axis limits)")
    ap.add_argument("--smooth", type=int, default=25, help="moving-average window [iterations]; raw shown faint")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    data = load(a.run)
    if a.list or a.out is None:
        print("\n".join(sorted(data)))
        return
    tags = [tuple(t.split(":", 1)) if ":" in t else (t, t) for t in a.tag] or [t for t in DEFAULT_TAGS if t[0] in data]
    clips = {c.rsplit(":", 2)[0]: tuple(map(float, c.rsplit(":", 2)[1:])) for c in a.clip}
    cols = min(len(tags), 3)
    rows = (len(tags) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5.2 * cols, 3.2 * rows), squeeze=False)
    for ax, (tag, label) in zip(axes.flat, tags):
        x, y = data[tag]
        ax.plot(x, y, color=SERIES, alpha=0.25, linewidth=1)
        ax.plot(x, smooth(y, a.smooth), color=SERIES, linewidth=2)
        ax.set_title(label, fontsize=11, color=INK, loc="left")
        if tag in clips:
            ax.set_ylim(*clips[tag])
        ax.grid(True, color=LINE, linewidth=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(LINE)
        ax.tick_params(colors=MUTED, labelsize=9)
        ax.set_xlabel("iteration", fontsize=9, color=MUTED)
        ax.annotate(f"{y[-1]:.3g}", (x[-1], smooth(y, a.smooth)[-1]), textcoords="offset points", xytext=(-4, 6),
                    ha="right", fontsize=9, color=INK)
    for ax in list(axes.flat)[len(tags):]:
        ax.axis("off")
    if a.title:
        fig.suptitle(a.title, x=0.01, ha="left", fontsize=13, color=INK)
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=130, facecolor="white")
    print(f"{a.out}: {', '.join(t for t, _ in tags)}")


if __name__ == "__main__":
    main()
