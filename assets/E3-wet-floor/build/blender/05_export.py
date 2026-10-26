# E3 wet floor, Blender step 5/5: export the tile to model.usd (Z-up, metres, textures copied to textures/;
# one box collider, low-friction physics material declared as tags) and model.glb; save model.blend with this scene only.
# Vars: SCENE, OUT.
import os
obs = assets()
for ob in obs:
    ob["asset_id"] = "E3"; ob["physics_friction"] = 0.3; ob["collider"] = "box"; ob["physics_material"] = "WetTile_mu0.3"
with ctx():
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.wm.usd_export(filepath=os.path.join(OUT, "model.usd"), selected_objects_only=True, export_materials=True,
                          export_uvmaps=True, export_normals=True, generate_preview_surface=True,
                          export_textures_mode="NEW", relative_paths=True, convert_orientation=False,
                          meters_per_unit=1.0, root_prim_path="/E3_wet_floor", export_custom_properties=True,
                          export_lights=False, export_cameras=False, convert_world_material=False)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "model.glb"), export_format="GLB", use_selection=True, use_active_scene=True,
                              export_materials="EXPORT", export_yup=True, export_cameras=False, export_extras=True)
path = os.path.join(OUT, "model.blend")
bpy.data.libraries.write(path, {sc}, path_remap="RELATIVE_ALL", fake_user=True, compress=True)
with bpy.data.libraries.load(path) as (src, _):
    print("blend scenes", src.scenes, "objects", sorted(src.objects), "images", src.images)
print("exported", sorted(f for f in os.listdir(OUT) if f.startswith("model.")))
