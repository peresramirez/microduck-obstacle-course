# F floor and lane, Blender step 3/5: preview-only staging (never exported): a darker surround so the 6 x 1.2 m lane
# reads, the 25 cm Microduck-sized marker in the start area, sun, sky-gradient world (polished floor reflects it),
# a wide camera down the whole lane and a close-up camera on the start line.
# Vars: SCENE.
import bmesh
ref = bpy.data.collections.new("F_preview_only"); ref["role"] = "preview_only"
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


add(box("Floor_preview", 10.0, 5.0, 0.01, (3.0, 0, -0.0060)), "floor", mat("DarkConcrete_preview", (0.30, 0.31, 0.32), 0.8))   # darker than the tile
duck = add(box("Microduck_25cm_marker", 0.10, 0.14, 0.25, (0.25, 0, 0.125)), "marker", mat("Marker_yellow", (1.0, 0.55, 0.02), 0.4))
bev = duck.modifiers.new("Bevel", "BEVEL"); bev.width = 0.02; bev.segments = 4; bev.affect = "EDGES"
txt = bpy.data.curves.new("Label", "FONT"); txt.body = "Microduck\n25 cm"; txt.size = 0.025
txt.align_x = "CENTER"; txt.align_y = "CENTER"
lab = add(bpy.data.objects.new("Label_preview", txt), "label", mat("Label_black", (0.02, 0.02, 0.02), 0.5))
lab.location = (0.3015, 0, 0.15); lab.rotation_euler = (math.radians(90), 0, math.radians(90))
sun_d = bpy.data.lights.new("Sun_preview", "SUN"); sun_d.energy = 3.2; sun_d.angle = math.radians(3)
sun = add(bpy.data.objects.new("Sun_preview", sun_d), "sun"); sun.rotation_euler = (math.radians(55), 0, math.radians(-150))
# sky gradient (bright pale horizon -> blue zenith): gives the polished floor something to reflect
w = bpy.data.worlds.new("F_world"); sc.world = w; w.use_nodes = True; wn = w.node_tree
coord = wn.nodes.new("ShaderNodeTexCoord"); sep = wn.nodes.new("ShaderNodeSeparateXYZ"); ramp = wn.nodes.new("ShaderNodeValToRGB")
wn.links.new(coord.outputs["Generated"], sep.inputs[0]); wn.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.92, 0.93, 0.95, 1)
ramp.color_ramp.elements[1].position = 0.4; ramp.color_ramp.elements[1].color = (0.25, 0.42, 0.75, 1)
wn.links.new(ramp.outputs["Color"], wn.nodes["Background"].inputs["Color"])
wn.nodes["Background"].inputs["Strength"].default_value = 0.8
sc.camera = camera("Cam_preview", "camera", (-1.6, -2.4, 1.9), (2.6, 0.0, 0.0), 32)
camera("Cam_detail", "camera_detail", (1.10, -0.70, 0.30), (0.33, 0.0, 0.06), 40)
with ctx():
    bpy.ops.object.select_all(action="DESELECT")
    area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.view3d.view_center_camera()
print("staged", sorted(o.name for o in ref.objects))
