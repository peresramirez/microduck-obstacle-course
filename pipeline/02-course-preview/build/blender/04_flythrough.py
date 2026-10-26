# Course preview, Blender step 4/4: animate the 25 cm marker along the layout.json route (riding over the hump, the steps
# and the wet tile; around the box) with a chase camera behind and above it; set up an 18 s, 24 fps, 1280x720 render;
# save course.blend (this scene only). The animation itself is rendered by a separate background Blender (build.sh),
# so the open Blender isn't blocked for minutes. Vars: SCENE, OUT, LAYOUT.
import os
place, route = placements(LAYOUT)
pts = [Vector((0.20, 0.0))] + [Vector(p) for p in route]           # start from the duck's spot in the start area
for _ in range(3):                                                  # Chaikin smoothing of the corners
    new = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        new += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
    pts = new + [pts[-1]]
seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
L = sum(seg)


def at(s):
    """Point and unit tangent at arc length s (linear extrapolation outside 0..L)."""
    if s <= 0:
        t = (pts[1] - pts[0]).normalized(); return pts[0] + t * s, t
    acc = 0.0
    for i, d in enumerate(seg):
        if acc + d >= s or i == len(seg) - 1:
            t = (pts[i + 1] - pts[i]).normalized(); return pts[i] + t * (s - acc), t
        acc += d


def ground(p):
    """Surface height under the route from the placed assets (spec values)."""
    x, y = p.x, p.y
    if abs(y) > 0.3:
        return 0.0
    e1, e2, e3 = place["E1"][0], place["E2"][0], place["E3"][0]
    if e1 <= x <= e1 + 1.0:
        return 0.033 / 2 * (1 - math.cos(2 * math.pi * (x - e1) / 1.0))
    if e2 <= x <= e2 + 1.2:
        return 0.020 if e2 + 0.2 <= x <= e2 + 1.0 else 0.010
    if e3 <= x <= e3 + 0.8:
        return 0.002
    return 0.0


fps, secs = 24, 18
sc.render.fps = fps; sc.frame_start, sc.frame_end = 1, fps * secs
marker = tagged("marker")
cam = bpy.data.objects.new("Cam_chase", bpy.data.cameras.new("Cam_chase")); cam.data.lens = 28; cam["role"] = "camera_chase"
next(c for c in sc.collection.children if c.get("role") == "preview_only").objects.link(cam)
for f in range(sc.frame_start, sc.frame_end + 1):
    s = L * (f - 1) / (sc.frame_end - 1)
    p, t = at(s)
    marker.location = (p.x, p.y, ground(p) + 0.125); marker.rotation_euler = (0, 0, math.atan2(t.y, t.x))
    marker.keyframe_insert("location", frame=f); marker.keyframe_insert("rotation_euler", frame=f)
    c, _ = at(s - 0.9); look, _ = at(s + 0.5)
    cam.location = (c.x, c.y - 0.35, 0.55)
    cam.rotation_euler = (Vector((look.x, look.y, 0.10)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
sc.camera = cam
r = sc.render; r.engine = "BLENDER_EEVEE"; r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
sc.eevee.taa_render_samples = 16; sc.eevee.use_raytracing = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
r.image_settings.file_format = "PNG"; r.filepath = os.path.join(OUT, "renders", "flythrough", "")
sc.frame_set(1)
path = os.path.join(OUT, "course.blend")
bpy.data.libraries.write(path, {sc}, path_remap="RELATIVE_ALL", fake_user=True, compress=True)
print("route length %.2f m, %d frames, saved %s" % (L, sc.frame_end, path))
