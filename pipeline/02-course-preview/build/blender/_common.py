# Shared by every course-preview Blender step; apps.py exec sends it in front of the step script.
# Vars: SCENE = scene name (created by 01_import.py).
import bpy, math
from mathutils import Vector

win = bpy.context.window_manager.windows[0]
area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
region = next(r for r in area.regions if r.type == "WINDOW")
sc = bpy.data.scenes.get(SCENE)


def ctx():
    # view3d operators need the window, area and its WINDOW region
    return bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region, scene=sc)


def frame(*obs):
    with ctx():
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.ops.view3d.view_selected()


def tagged(role):
    # objects are found by a custom "role" property, so a rebuild in another scene never picks up the original
    return next(o for o in sc.objects if o.get("role") == role)


def assets():
    return sorted((o for o in sc.objects if o.get("role") == "asset"), key=lambda o: o.name)

import json


def placements(layout_path):
    """Asset id -> (x, y, model.usd folder) in Blender world coordinates: x along the lane, y = 0 on the lane
    centre. layout.json gives each item's corner (x, y) and size (w, d), with y running 0-1.2 across the lane;
    every asset's origin is the bottom-centre of its start edge, so it goes at (x, y + d/2 - 0.6)."""
    lay = json.load(open(layout_path))
    half = lay["floor"]["d"] / 2
    out = {"F": (0.0, 0.0, "F-floor")}
    folders = {"E1": "E1-gentle-hump", "E2": "E2-low-steps", "E3": "E3-wet-floor", "E4": "E4-box"}
    for it in lay["items"]:
        if it["id"] in folders:
            out[it["id"]] = (it["x"], it["y"] + it["d"] / 2 - half, folders[it["id"]])
    return out, [(x, y - half) for x, y in lay["route"]]
