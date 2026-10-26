# E1 gentle hump, Blender step 3/5: preview-only staging (never exported): concrete floor,
# 25 cm Microduck-sized marker with a label, low sun, world light, camera.
# Vars: SCENE.
import bmesh
ref = bpy.data.collections.new("E1_preview_only"); ref["role"] = "preview_only"
sc.collection.children.link(ref)


def mat(name, rgb, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m


def add(ob, role, m=None):
    ref.objects.link(ob); ob["role"] = role
    if m:
        ob.data.materials.append(m)
    return ob


def box(name, sx, sy, sz, loc):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.scale = (sx, sy, sz); ob.location = loc
    return ob


add(box("Floor_preview", 4.0, 3.0, 0.01, (0.5, 0, -0.0051)), "floor", mat("Concrete_preview", (0.55, 0.56, 0.57), 0.75))
# Microduck: 25 cm tall, 14 cm wide; stands at the start edge facing +x
duck = add(box("Microduck_25cm_marker", 0.10, 0.14, 0.25, (-0.15, 0, 0.125)), "marker", mat("Marker_yellow", (1.0, 0.55, 0.02), 0.4))
bev = duck.modifiers.new("Bevel", "BEVEL"); bev.width = 0.02; bev.segments = 4; bev.affect = "EDGES"
txt = bpy.data.curves.new("Label", "FONT"); txt.body = "Microduck\n25 cm"; txt.size = 0.025
txt.align_x = "CENTER"; txt.align_y = "CENTER"
lab = add(bpy.data.objects.new("Label_preview", txt), "label", mat("Label_black", (0.02, 0.02, 0.02), 0.5))
lab.location = (-0.0985, 0, 0.15); lab.rotation_euler = (math.radians(90), 0, math.radians(90))   # on the marker's +x face
sun_d = bpy.data.lights.new("Sun_preview", "SUN"); sun_d.energy = 3.6; sun_d.angle = math.radians(3)
sun = add(bpy.data.objects.new("Sun_preview", sun_d), "sun"); sun.rotation_euler = (math.radians(74), 0, math.radians(-150))   # low, raking: shows the 3.3 cm crest
w = bpy.data.worlds.new("E1_world"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.78, 0.82, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
cam = add(bpy.data.objects.new("Cam_preview", bpy.data.cameras.new("Cam_preview")), "camera"); cam.data.lens = 38
cam.location = (1.45, -1.05, 0.38)
cam.rotation_euler = (Vector((0.38, 0.0, 0.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
with ctx():
    bpy.ops.object.select_all(action="DESELECT")
    area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.view3d.view_center_camera()
print("staged", [o.name for o in ref.objects])
