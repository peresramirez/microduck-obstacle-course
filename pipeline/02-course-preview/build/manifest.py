"""Write course_manifest.json: what phase 5 (Isaac Sim scene) needs for each asset, read from the exported USDs
(userProperties tags written by Blender) and layout.json, so nothing is retyped by hand.

Run from isaac-obstacle-course/:
  uv run --no-project --with usd-core python pipeline/02-course-preview/build/manifest.py
"""

import json
from pathlib import Path

from pxr import Usd, UsdGeom

ROOT = Path(__file__).resolve().parents[3]
FOLDERS = {"F": "F-floor", "E1": "E1-gentle-hump", "E2": "E2-low-steps", "E3": "E3-wet-floor", "E4": "E4-box"}
lay = json.loads((ROOT / "pipeline/01-plan/layout.json").read_text())
half = lay["floor"]["d"] / 2
items = {it["id"]: it for it in lay["items"]}
out = {"version": 1, "date": "2026-10-26", "units": "metres, Z-up",
       "frames": {"layout": "layout.json: x along the lane 0-6, y across 0-1.2, items given by their corner",
                  "lane": "x along the lane, y = 0 on the lane centre (Blender course preview, check_course.py)"},
       "robot": {"usd": "microduck_allcollisions[_backlash].usd (MICRODUCK_ALLCOLLISIONS_CFG)",
                 "why": "microduck_walk.usd has sole colliders only; its body would pass through E4"},
       "open_items": ["Verify how Newton/MJWarp combines foot and ground friction (MuJoCo default is max, which would cancel E3's μ 0.3)",
                      "Pin Isaac Lab main to a commit (727e4e43a on 2026-10-26); the develop branch is gone",
                      "Route ↔ E4 side clearance is 8.8 cm; widen the detour if training clips the box"],
       "assets": []}
for aid, folder in FOLDERS.items():
    st = Usd.Stage.Open(str(ROOT / "assets" / folder / "model.usd"))
    parts = []
    for p in st.Traverse():
        tags = {a.GetName().split(":")[-1]: a.Get() for a in p.GetAttributes() if a.GetName().startswith("userProperties:")}
        if "collider" in tags:
            r = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]).ComputeWorldBound(p).ComputeAlignedRange()
            parts.append({"prim": str(p.GetPath()), "collider": tags["collider"], "static_friction": tags.get("physics_friction"),
                          "dynamic_friction": tags.get("physics_friction"), "restitution": 0.0,
                          "physics_material": tags.get("physics_material", f"mu{tags.get('physics_friction')}"),
                          "bounds_local": [list(r.GetMin()), list(r.GetMax())]})
    if aid == "F":
        lx, ly = 0.0, half
    else:
        it = items[aid]; lx, ly = it["x"], it["y"] + it["d"] / 2
    out["assets"].append({"id": aid, "usd": f"assets/{folder}/model.usd", "default_prim": str(st.GetDefaultPrim().GetPath()),
                          "origin_layout": [lx, ly, 0.0], "origin_lane": [lx, ly - half, 0.0], "body": "static",
                          "notes": f"assets/{folder}/NOTES.md", "parts": parts})
(ROOT / "pipeline/02-course-preview/course_manifest.json").write_text(json.dumps(out, indent=2) + "\n")
for a in out["assets"]:
    print(a["id"], a["origin_layout"], [(p["collider"], p["static_friction"]) for p in a["parts"]])
