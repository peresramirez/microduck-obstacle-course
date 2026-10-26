"""Put two videos side by side with a label bar over each (e.g. before / after training).

ffmpeg here has no ``drawtext``, so the labels are rendered as PNG with headless Google Chrome and overlaid.
Run from isaac-obstacle-course/ on the Mac:

    uv run --no-project python tools/compare_videos.py LEFT.mp4 "Left label" RIGHT.mp4 "Right label" OUT.mp4 \\
        [--width 960]
"""

import argparse
import html
import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def label_png(text: str, width: int, height: int, out: Path, colour: str) -> None:
    page = out.with_suffix(".html")
    page.write_text(
        f"""<html><body style="margin:0;width:{width}px;height:{height}px;background:{colour};display:flex;
        align-items:center;justify-content:center;font:600 {height // 2}px -apple-system,Helvetica,sans-serif;
        color:#fff">{html.escape(text)}</body></html>"""
    )
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={width},{height}",
                    f"--screenshot={out}", page.as_uri()], check=True, capture_output=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("left", type=Path)
    ap.add_argument("left_label")
    ap.add_argument("right", type=Path)
    ap.add_argument("right_label")
    ap.add_argument("out", type=Path)
    ap.add_argument("--width", type=int, default=960, help="width of each half [px]")
    a = ap.parse_args()
    w, bar = a.width, 64
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        label_png(a.left_label, w, bar, tmp / "l.png", "#7c2d12")
        label_png(a.right_label, w, bar, tmp / "r.png", "#14532d")
        filt = (f"[0:v]scale={w}:-2,setsar=1[a];[1:v]scale={w}:-2,setsar=1[b];"
                f"[2:v][a]vstack[la];[3:v][b]vstack[rb];[la][rb]hstack=shortest=0,format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(a.left), "-i", str(a.right),
                        "-loop", "1", "-i", str(tmp / "l.png"), "-loop", "1", "-i", str(tmp / "r.png"),
                        "-filter_complex", filt, "-map", "[v]", "-c:v", "libx264", "-crf", "20", "-r", "30",
                        "-t", str(max(_duration(a.left), _duration(a.right))), str(a.out)], check=True)
    print(f"{a.out}: {_duration(a.out):.1f} s")


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


if __name__ == "__main__":
    main()
