# E4 box, Blender step 3/5: preview-only staging (never exported): concrete floor, 25 cm Microduck-sized marker
# beside the box (the duck walks around it), low sun, world light, a wide camera and a close-up camera on the hand-hole.
# Vars: SCENE.
import bmesh
ref = bpy.data.collections.new("E4_preview_only"); ref["role"] = "preview_only"
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


def camera(name, role, loc, target, lens):
    cam = add(bpy.data.objects.new(name, bpy.data.cameras.new(name)), role); cam.data.lens = lens
    cam.location = loc; cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


add(box("Floor_preview", 3.0, 2.5, 0.01, (0.1, 0, -0.0051)), "floor", mat("Concrete_preview", (0.55, 0.56, 0.57), 0.75))
duck = add(box("Microduck_25cm_marker", 0.10, 0.14, 0.25, (-0.14, -0.12, 0.125)), "marker", mat("Marker_yellow", (1.0, 0.55, 0.02), 0.4))
bev = duck.modifiers.new("Bevel", "BEVEL"); bev.width = 0.02; bev.segments = 4; bev.affect = "EDGES"
txt = bpy.data.curves.new("Label", "FONT"); txt.body = "Microduck\n25 cm"; txt.size = 0.025
txt.align_x = "CENTER"; txt.align_y = "CENTER"
lab = add(bpy.data.objects.new("Label_preview", txt), "label", mat("Label_black", (0.02, 0.02, 0.02), 0.5))
lab.location = (-0.0885, -0.12, 0.15); lab.rotation_euler = (math.radians(90), 0, math.radians(90))   # on the marker's +x face
sun_d = bpy.data.lights.new("Sun_preview", "SUN"); sun_d.energy = 3.6; sun_d.angle = math.radians(3)
sun = add(bpy.data.objects.new("Sun_preview", sun_d), "sun"); sun.rotation_euler = (math.radians(70), 0, math.radians(-140))
w = bpy.data.worlds.new("E4_world"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.78, 0.82, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
sc.camera = camera("Cam_preview", "camera", (0.80, -0.95, 0.42), (0.04, 0.0, 0.09), 40)
camera("Cam_detail", "camera_detail", (0.20, -0.44, 0.15), (0.10, -0.10, 0.10), 50)
with ctx():
    bpy.ops.object.select_all(action="DESELECT")
    area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.view3d.view_center_camera()
print("staged", sorted(o.name for o in ref.objects))
