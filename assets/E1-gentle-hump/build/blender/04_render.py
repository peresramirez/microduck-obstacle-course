# E1 gentle hump, Blender step 4/5: render preview.png (Eevee, 1920x1080, AgX medium-high contrast).
# Vars: SCENE, OUT.
import os
r = sc.render; r.engine = "BLENDER_EEVEE"; r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
r.filepath = os.path.join(OUT, "preview.png"); r.image_settings.file_format = "PNG"
with ctx():
    bpy.ops.render.render(write_still=True, scene=sc.name)
print("rendered", r.filepath)
