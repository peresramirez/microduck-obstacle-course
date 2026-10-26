# Course preview, Blender step 1/4: new scene; import the five exported model.usd files (F, E1-E4) and place each at its
# layout.json position. Textures are referenced from each asset's own textures/ folder (IMPORT_NONE), because they all
# share file names (basecolor.png) and the default "use existing" mode would give every asset the first one's texture.
# Vars: SCENE, ASSETS (assets/ folder, absolute), LAYOUT (layout.json, absolute).
import os
assert sc is None, f"scene {SCENE} already exists; pick another SCENE"
sc = bpy.data.scenes.new(SCENE)
win.scene = sc
sc.unit_settings.system = "METRIC"; sc.unit_settings.length_unit = "CENTIMETERS"
place, route = placements(LAYOUT)
for aid in ("F", "E1", "E2", "E3", "E4"):
    x, y, folder = place[aid]
    coll = bpy.data.collections.new(f"Course_{aid}"); coll["role"] = "course_asset"; sc.collection.children.link(coll)
    before = set(bpy.data.objects)
    with ctx():
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[coll.name]
        bpy.ops.wm.usd_import(filepath=os.path.join(ASSETS, folder, "model.usd"), import_textures_mode="IMPORT_NONE",
                              create_world_material=False, import_cameras=False, import_lights=False)
    new = set(bpy.data.objects) - before
    for o in new:
        o["course_asset"] = aid
        if o.parent not in new:
            o.location.x += x; o.location.y += y
    meshes = [o for o in new if o.type == "MESH"]
    bpy.context.view_layer.update()
    bb = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    print(aid, "objects", len(new), "meshes", len(meshes), "x %.3f-%.3f y %.3f-%.3f z %.3f-%.3f" % (
        min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb), max(v.z for v in bb)),
        "images", sorted({n.image.filepath.split("assets/")[-1] for o in meshes for s in o.material_slots if s.material and s.material.use_nodes
                          for n in s.material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image}))
area.spaces.active.shading.type = "MATERIAL"
area.spaces.active.region_3d.view_rotation = __import__("mathutils").Euler((math.radians(62), 0, math.radians(30))).to_quaternion()
frame(*[o for o in sc.objects if o.type == "MESH"])
