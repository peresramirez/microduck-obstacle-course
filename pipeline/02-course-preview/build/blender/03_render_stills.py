# Course preview, Blender step 3/4: render the overview (with the 25 cm marker at the start) and the four duck-eye views
# (marker hidden, the camera is where the duck's head would be). Eevee with ray tracing, 1920x1080. Vars: SCENE, OUT.
import os
r = sc.render; r.engine = "BLENDER_EEVEE"; r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
sc.eevee.taa_render_samples = 64; sc.eevee.use_raytracing = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
r.image_settings.file_format = "PNG"
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
marker = tagged("marker")
for role, fname, show_marker in [("camera", "overview.png", True)] + [(f"camera_eye_{i}", f"duck-eye-{i}.png", False) for i in range(1, 5)]:
    sc.camera = tagged(role); marker.hide_render = not show_marker
    r.filepath = os.path.join(OUT, "renders", fname)
    with ctx():
        bpy.ops.render.render(write_still=True, scene=sc.name)
    print("rendered", fname)
marker.hide_render = False; sc.camera = tagged("camera")
