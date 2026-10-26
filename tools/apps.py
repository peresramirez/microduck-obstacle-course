"""Drive FreeCAD and Blender through their MCP add-ons, and record their windows from inside the app.

Recording captures only the application's own window (no desktop, other apps, notifications or
macOS title bar) and needs no macOS screen-recording permission:
  - FreeCAD: Qt grab of the main window, with the 3D view rendered by saveImage() pasted in;
  - Blender: Blender's own window screenshot operator.

Run from isaac-obstacle-course/:
  uv run --no-project python tools/apps.py exec freecad|blender SCRIPT.py [MORE.py ...] [--var NAME=VALUE ...]
  uv run --no-project python tools/apps.py rec-start freecad|blender NAME [--fps 2]
  uv run --no-project python tools/apps.py rec-stop  freecad|blender NAME [--speed 1] [--delete-frames]

exec joins the scripts in order into one block and puts `NAME = "VALUE"` lines before it, so build
scripts can take paths and names without editing them.
Frames are kept in videos/<phase>/frames/NAME/ (raw source for the showreel); the clip goes to videos/<phase>/NAME.mp4,
with <phase> taken from the name's two-digit prefix (see PHASE_DIRS)
(1920 px wide, H.264, 30 fps).
"""

import argparse
import json
import shutil
import socket
import subprocess
import sys
import xmlrpc.client
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
# clips live in one folder per phase, chosen from the clip name's prefix ("02-1-e1-freecad" -> phase-2-assets/)
PHASE_DIRS = {"00": "phase-0-tools", "01": "phase-1-plan", "02": "phase-2-assets", "03": "phase-3-workstation",
              "04": "phase-4-baseline", "05": "phase-5-scene", "06": "phase-6-train", "07": "phase-7-validate"}


def phase_dir(name: str) -> Path:
    return VIDEOS / PHASE_DIRS.get(name[:2], "misc")


def freecad_exec(code: str) -> str:
    res = xmlrpc.client.ServerProxy("http://127.0.0.1:9875", allow_none=True).execute_code(code)
    if not res.get("success"):
        sys.exit(f"FreeCAD error: {res.get('error')}")
    return res.get("message", "")


def blender_exec(code: str) -> str:
    with socket.create_connection(("127.0.0.1", 9876), timeout=300) as s:
        s.sendall(json.dumps({"type": "execute_code", "params": {"code": code}}).encode())
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            try:
                res = json.loads(buf.decode())
                break
            except json.JSONDecodeError:
                continue
    if res.get("status") != "success":
        sys.exit(f"Blender error: {res.get('message') or res}")
    return res["result"].get("result", "")


RUN = {"freecad": freecad_exec, "blender": blender_exec}

FREECAD_START = """
import os, FreeCADGui
from PySide import QtCore, QtGui, QtWidgets
frames, interval = {frames!r}, {interval}
os.makedirs(frames, exist_ok=True)
tmp = os.path.join(frames, "_view.png")
state = {{"n": len([f for f in os.listdir(frames) if f.endswith(".jpg")])}}

def grab():
    try:
        mw = FreeCADGui.getMainWindow()
        img = mw.grab()
        dpr = img.devicePixelRatio()
        gui_doc = FreeCADGui.ActiveDocument
        view = gui_doc.ActiveView if gui_doc else None
        if view is not None and hasattr(view, "saveImage"):
            p = QtGui.QPainter(img)
            for w in mw.findChildren(QtWidgets.QWidget):
                if w.inherits("QOpenGLWidget") and w.isVisible() and w.width() > 200:
                    view.saveImage(tmp, int(w.width() * dpr), int(w.height() * dpr), "Current")
                    p.drawImage(QtCore.QRect(w.mapTo(mw, QtCore.QPoint(0, 0)), w.size()), QtGui.QImage(tmp))
            p.end()
        img.save(os.path.join(frames, "%06d.jpg" % state["n"]), "JPG", 90)
        state["n"] += 1
    except Exception as e:
        print("recorder:", e)

old = getattr(FreeCADGui, "_mcp_recorder", None)
if old: old.stop()
t = QtCore.QTimer()
t.timeout.connect(grab)
t.start(interval)
FreeCADGui._mcp_recorder = t
grab()
print("recording", frames)
"""

FREECAD_STOP = """
import FreeCADGui
t = getattr(FreeCADGui, "_mcp_recorder", None)
if t: t.stop(); FreeCADGui._mcp_recorder = None
print("stopped")
"""

BLENDER_START = """
import bpy, os
frames, interval = {frames!r}, {interval_s}
os.makedirs(frames, exist_ok=True)
state = bpy.app.driver_namespace.setdefault("mcp_recorder", {{}})
state.update(active=True, n=len([f for f in os.listdir(frames) if f.endswith(".png")]), frames=frames)

def grab():
    st = bpy.app.driver_namespace.get("mcp_recorder", {{}})
    if not st.get("active"):
        return None
    try:
        win = bpy.context.window_manager.windows[0]
        area = max(win.screen.areas, key=lambda a: a.width * a.height)
        with bpy.context.temp_override(window=win, screen=win.screen, area=area):
            bpy.ops.screen.screenshot(filepath=os.path.join(st["frames"], "%06d.png" % st["n"]))
        st["n"] += 1
    except Exception as e:
        print("recorder:", e)
    return {interval_s}

bpy.app.timers.register(grab, first_interval=0.0)
print("recording", frames)
"""

BLENDER_STOP = """
import bpy
st = bpy.app.driver_namespace.get("mcp_recorder")
if st: st["active"] = False
print("stopped")
"""


def encode(frames: Path, out: Path, fps: float, speed: float) -> None:
    files = sorted(p for p in frames.iterdir() if p.suffix in (".jpg", ".png") and not p.name.startswith("_"))
    if not files:
        sys.exit(f"No frames in {frames}")
    ext = files[0].suffix
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps * speed),
        "-pattern_type", "glob", "-i", str(frames / f"*{ext}"),
        # even width/height for H.264; 1920 px wide keeps text readable on YouTube
        "-vf", "scale=1920:-2:flags=lanczos,format=yuv420p", "-r", "30",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow", str(out),
    ], check=True)
    secs = len(files) / (fps * speed)
    print(f"{out}  ({len(files)} frames, {secs:.1f} s)")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("exec"); e.add_argument("app", choices=RUN); e.add_argument("scripts", type=Path, nargs="+")
    e.add_argument("--var", action="append", default=[], metavar="NAME=VALUE", help="defined as a string before the scripts")
    s = sub.add_parser("rec-start"); s.add_argument("app", choices=RUN); s.add_argument("name"); s.add_argument("--fps", type=float, default=2.0)
    t = sub.add_parser("rec-stop"); t.add_argument("app", choices=RUN); t.add_argument("name")
    t.add_argument("--fps", type=float, default=2.0, help="capture rate used at rec-start")
    t.add_argument("--speed", type=float, default=1.0, help=">1 plays faster than real time")
    t.add_argument("--delete-frames", action="store_true", help="remove the raw frames after encoding")
    a = ap.parse_args()

    if a.cmd == "exec":
        head = "".join(f"{k} = {v!r}\n" for k, v in (kv.split("=", 1) for kv in a.var))
        print(RUN[a.app](head + "\n".join(p.read_text() for p in a.scripts)))
        return
    frames = phase_dir(a.name) / "frames" / a.name
    if a.cmd == "rec-start":
        code = (FREECAD_START.format(frames=str(frames), interval=int(1000 / a.fps)) if a.app == "freecad"
                else BLENDER_START.format(frames=str(frames), interval_s=1.0 / a.fps))
        print(RUN[a.app](code))
    else:
        print(RUN[a.app](FREECAD_STOP if a.app == "freecad" else BLENDER_STOP))
        phase_dir(a.name).mkdir(parents=True, exist_ok=True)
        encode(frames, phase_dir(a.name) / f"{a.name}.mp4", a.fps, a.speed)
        if a.delete_frames:
            shutil.rmtree(frames)


if __name__ == "__main__":
    main()
