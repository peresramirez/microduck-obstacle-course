"""Record one Mac app window (never the full screen) to an MP4, e.g. the Isaac Sim WebRTC Streaming Client.

Captures the window by its window id with `screencapture -l` several times a second, then encodes the frames with
ffmpeg. Needs macOS Screen Recording permission for the app running this (Terminal); without it the frames are black.
Only the named window is captured: no desktop, other apps or notifications.

Run from isaac-obstacle-course/:
  uv run --no-project --with pyobjc-framework-Quartz python tools/record_window.py \
      "Isaac Sim WebRTC Streaming Client" videos/phase-4-baseline/04-webrtc-stream.mp4 --seconds 60 [--fps 4] [--speed 1]
Stop early with Ctrl+C (or by creating the file NAME.stop next to the output); frames recorded so far are kept.
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import Quartz


def window_id(owner: str) -> int:
    """Largest on-screen, normal-layer window of the app whose name contains ``owner``."""
    opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    def matches(w) -> bool:
        # macOS truncates owner names to 31 characters ("Isaac Sim WebRTC Streaming Clie"), so also accept a
        # truncated owner name or a matching window title
        name, title = str(w.get("kCGWindowOwnerName", "")), str(w.get("kCGWindowName", ""))
        return owner in name or (len(name) >= 20 and owner.startswith(name)) or owner in title

    wins = [w for w in Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID)
            if matches(w) and w.get("kCGWindowLayer") == 0]
    if not wins:
        sys.exit(f"no on-screen window for {owner!r}")
    big = max(wins, key=lambda w: w["kCGWindowBounds"]["Width"] * w["kCGWindowBounds"]["Height"])
    return int(big["kCGWindowNumber"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("owner")
    ap.add_argument("output", type=Path)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--fps", type=float, default=4)
    ap.add_argument("--speed", type=float, default=1.0, help=">1 plays faster than real time")
    ap.add_argument("--keep-frames", action="store_true")
    a = ap.parse_args()
    wid = window_id(a.owner)
    frames = a.output.with_suffix("").parent / "frames" / a.output.stem
    frames.mkdir(parents=True, exist_ok=True)
    stop = a.output.with_suffix(".stop")
    print(f"recording window {wid} ({a.owner}) -> {frames}", flush=True)
    n, t0 = 0, time.time()
    try:
        while time.time() - t0 < a.seconds and not stop.exists():
            t = time.time()
            subprocess.run(["screencapture", "-x", "-o", "-l", str(wid), str(frames / f"{n:06d}.png")], check=False)
            n += 1
            time.sleep(max(0.0, 1.0 / a.fps - (time.time() - t)))
    except KeyboardInterrupt:
        pass
    stop.unlink(missing_ok=True)
    real_fps = n / max(time.time() - t0, 1e-6)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", f"{real_fps * a.speed:.3f}", "-pattern_type", "glob",
                    "-i", str(frames / "*.png"), "-vf", "scale=1920:-2:flags=lanczos,format=yuv420p", "-r", "30",
                    "-c:v", "libx264", "-crf", "18", str(a.output)], check=True)
    print(f"{a.output}: {n} frames over {time.time() - t0:.0f} s ({real_fps:.1f} fps captured)")
    if not a.keep_frames:
        shutil.rmtree(frames)


if __name__ == "__main__":
    main()
