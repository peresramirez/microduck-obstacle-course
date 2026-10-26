# F floor and lane, Blender step 1/5: new scene, import FreeCAD's floor mesh, bake mm -> m, make sure it faces up.
# Vars: SCENE, OUT (asset folder with freecad-mesh.stl).
import os
assert sc is None, f"scene {SCENE} already exists; pick another SCENE"
sc = bpy.data.scenes.new(SCENE)
win.scene = sc                                  # other scenes are left untouched
sc.unit_settings.system = "METRIC"; sc.unit_settings.length_unit = "CENTIMETERS"
with ctx():
    bpy.ops.wm.stl_import(filepath=os.path.join(OUT, "freecad-mesh.stl"), global_scale=0.001)
ob = next(o for o in sc.objects if o.type == "MESH")
ob.name = ob.data.name = "F_LaneFloor"
ob["role"] = "asset"
ob.data.transform(ob.matrix_basis); ob.matrix_basis.identity()   # vertices in metres
if sum(p.normal.z for p in ob.data.polygons) < 0:                 # the walking side must face +z
    ob.data.flip_normals()
ob.data.shade_flat()
area.spaces.active.shading.type = "SOLID"
area.spaces.active.region_3d.view_rotation = __import__("mathutils").Euler((math.radians(65), 0, math.radians(30))).to_quaternion()
frame(ob)
print("imported", ob.name, "dims_m", [round(x, 4) for x in ob.dimensions], "scale", tuple(ob.scale),
      "faces", len(ob.data.polygons), "normals z", [round(p.normal.z, 3) for p in ob.data.polygons])
