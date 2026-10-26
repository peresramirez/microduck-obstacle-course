# E2 low steps, Blender step 1/5: new scene, import one mesh per sheet, bake mm -> m into the vertices.
# Vars: SCENE, OUT (asset folder with freecad-mesh-bottom.stl / -top.stl).
import os
assert sc is None, f"scene {SCENE} already exists; pick another SCENE"
sc = bpy.data.scenes.new(SCENE)
win.scene = sc                                  # other scenes are left untouched
sc.unit_settings.system = "METRIC"; sc.unit_settings.length_unit = "CENTIMETERS"
for stl, name in (("freecad-mesh-bottom.stl", "E2_BottomSheet"), ("freecad-mesh-top.stl", "E2_TopSheet")):
    before = set(sc.objects)
    with ctx():
        bpy.ops.wm.stl_import(filepath=os.path.join(OUT, stl), global_scale=0.001)
    ob = (set(sc.objects) - before).pop()
    ob.name = ob.data.name = name
    ob["role"] = "asset"
    # the STL importer puts 0.001 on the object; bake it so vertices (and UVs, USD) are in metres
    ob.data.transform(ob.matrix_basis); ob.matrix_basis.identity()
    ob.data.shade_flat()
area.spaces.active.shading.type = "SOLID"
area.spaces.active.region_3d.view_rotation = __import__("mathutils").Euler((math.radians(70), 0, math.radians(35))).to_quaternion()
frame(*assets())
for ob in assets():
    b = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    print("imported", ob.name, "x", round(min(v.x for v in b), 4), round(max(v.x for v in b), 4),
          "z", round(min(v.z for v in b), 4), round(max(v.z for v in b), 4), "faces", len(ob.data.polygons), "scale", tuple(ob.scale))
