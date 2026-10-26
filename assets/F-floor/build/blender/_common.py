# Shared by every F Blender step; apps.py exec sends it in front of the step script.
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
