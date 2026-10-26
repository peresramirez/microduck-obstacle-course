# E3 wet floor, Blender step 4/5: render preview.png (wide) and preview-detail.png (low close-up with reflections).
# Eevee, 1920x1080, AgX medium-high contrast. Vars: SCENE, OUT.
import os
r = sc.render; r.engine = "BLENDER_EEVEE"; r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
sc.eevee.taa_render_samples = 64
sc.eevee.use_raytracing = True                  # screen-space reflections, so the puddles mirror the marker
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
r.image_settings.file_format = "PNG"
for role, fname in (("camera", "preview.png"), ("camera_detail", "preview-detail.png")):
    sc.camera = tagged(role)
    r.filepath = os.path.join(OUT, fname)
    with ctx():
        bpy.ops.render.render(write_still=True, scene=sc.name)
    print("rendered", r.filepath)
sc.camera = tagged("camera")
