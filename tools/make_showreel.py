"""Build a showreel video from a JSON sequence of title cards, stills and app clips.

Each segment becomes a 1920x1080, 30 fps, H.264 part with identical settings, then the parts are joined without
re-encoding. Text (title cards, the small label on clips and stills) is laid out as HTML and captured with headless
Chrome, because this ffmpeg build has no drawtext filter. Labels are captured with a transparent background and
overlaid. No audio.

Sequence format (see showreel/phase2.json):
  {"card": {"kicker", "title", "lines": [...], "pills": [...]}, "seconds": 5}
  {"clip": "videos/x.mp4", "speed": 1.5, "label": "..."}        # speed > 1 plays faster
  {"still": "path/to/image.png", "seconds": 3, "label": "..."}

Run from isaac-obstacle-course/:
  uv run --no-project python tools/make_showreel.py showreel/phase2.json
Work files (card HTML/PNG, parts) go to showreel/build/<name>/ (git-ignored parts: *.mp4).
"""

import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_CSS = """
* { box-sizing: border-box; margin: 0; }
html, body { width: 1920px; height: 1080px; overflow: hidden; }
body { font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; }
"""
CARD = """<!doctype html><html><head><meta charset="utf-8"><style>{css}
body {{ background: #141412; color: #ecebe6; padding: 150px 170px; display: flex; flex-direction: column; }}
.kicker {{ color: #fb923c; font-size: 40px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: 104px; line-height: 1.08; margin: 22px 0 46px; font-weight: 750; }}
p {{ font-size: 44px; line-height: 1.45; color: #b9b6ad; max-width: 1500px; }}
.pills {{ display: flex; gap: 22px; margin-top: 56px; flex-wrap: wrap; }}
.pill {{ border: 2px solid #4a4843; border-radius: 999px; padding: 12px 32px; font-size: 38px; color: #ecebe6; }}
footer {{ margin-top: auto; font-size: 28px; color: #77746c; border-top: 2px solid #2c2b28; padding-top: 28px; }}
</style></head><body>
<div class="kicker">{kicker}</div><h1>{title}</h1>{lines}<div class="pills">{pills}</div><footer>{footer}</footer>
</body></html>"""
LABEL = """<!doctype html><html><head><meta charset="utf-8"><style>{css}
body {{ background: transparent; }}
.label {{ position: absolute; left: 40px; bottom: 40px; background: rgba(20,20,18,.82); color: #ecebe6; font-size: 30px;
          padding: 14px 26px; border-radius: 12px; border-left: 6px solid #fb923c; max-width: 1700px; }}
.speed {{ color: #fb923c; font-weight: 700; margin-left: 14px; }}
</style></head><body><div class="label">{text}{speed}</div></body></html>"""


def chrome_png(html_path: Path, png: Path, transparent: bool) -> None:
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
           "--window-size=1920,1080", f"--screenshot={png}"]
    if transparent:
        cmd.append("--default-background-color=00000000")
    subprocess.run(cmd + [html_path.as_uri()], check=True, capture_output=True)


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]))


def main() -> None:
    seq_path = Path(sys.argv[1])
    seq = json.loads(seq_path.read_text())
    W, H = seq["size"]; fps = seq["fps"]
    work = ROOT / "showreel" / "build" / seq_path.stem
    work.mkdir(parents=True, exist_ok=True)
    enc = ["-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-an"]
    # every source is scaled to fit 1920x1080 and padded (app clips are 1920x1056/1060)
    fit = f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x141412,setsar=1"
    parts, total = [], 0.0
    for i, s in enumerate(seq["segments"]):
        part = work / f"part-{i:03d}.mp4"
        if "card" in s:
            c = s["card"]
            page = CARD.format(css=BASE_CSS, kicker=html.escape(c["kicker"]), title=html.escape(c["title"]),
                               lines="".join(f"<p>{html.escape(l)}</p>" for l in c.get("lines", [])),
                               pills="".join(f'<span class="pill">{html.escape(p)}</span>' for p in c.get("pills", [])),
                               footer=html.escape(seq["footer"]))
            (work / f"card-{i:03d}.html").write_text(page)
            png = work / f"card-{i:03d}.png"
            chrome_png(work / f"card-{i:03d}.html", png, transparent=False)
            secs = s["seconds"]
            ffmpeg("-loop", "1", "-t", str(secs), "-i", str(png), "-vf", f"{fit},fade=t=in:d=0.4,fade=t=out:st={secs - 0.4}:d=0.4", *enc, str(part))
        else:
            src = ROOT / (s.get("clip") or s["still"])
            speed = s.get("speed", 1.0)
            label_png = None
            if s.get("label"):
                sp = f'<span class="speed">{speed:g}×</span>' if "clip" in s and speed != 1 else ""
                (work / f"label-{i:03d}.html").write_text(LABEL.format(css=BASE_CSS, text=html.escape(s["label"]), speed=sp))
                label_png = work / f"label-{i:03d}.png"
                chrome_png(work / f"label-{i:03d}.html", label_png, transparent=True)
            if "clip" in s:
                secs = duration(src) / speed
                inputs = ["-i", str(src)]
                base = f"[0:v]setpts=PTS/{speed},{fit}[v]"
            else:
                secs = s["seconds"]
                inputs = ["-loop", "1", "-t", str(secs), "-i", str(src)]
                base = f"[0:v]{fit},fade=t=in:d=0.3,fade=t=out:st={secs - 0.3}:d=0.3[v]"
            if label_png:
                graph = f"{base};[v][1:v]overlay=0:0:format=auto[o]"
                ffmpeg(*inputs, "-loop", "1", "-i", str(label_png), "-filter_complex", graph, "-map", "[o]",
                       "-t", f"{secs:.3f}", *enc, str(part))
            else:
                ffmpeg(*inputs, "-filter_complex", base, "-map", "[v]", "-t", f"{secs:.3f}", *enc, str(part))
        parts.append(part)
        total += duration(part)
        print(f"{i:02d} {list(k for k in ('card', 'clip', 'still') if k in s)[0]:5s} {duration(part):6.1f} s  "
              f"{s.get('clip') or s.get('still') or s['card']['title']}")
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = ROOT / seq["output"]
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out))
    print(f"{out}  {duration(out):.1f} s ({duration(out) / 60:.1f} min), {len(parts)} segments, parts sum {total:.1f} s")


if __name__ == "__main__":
    main()
