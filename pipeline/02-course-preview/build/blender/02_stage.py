# Course preview, Blender step 2/4: preview-only staging around the assembled course (never exported): darker surround,
# sun, sky-gradient world (polished floor and wet tile reflect it), the 25 cm Microduck-sized marker at the start,
# an overview camera and four duck-eye cameras (0.20 m up, the head height of a 25 cm robot) along the route.
# Vars: SCENE, LAYOUT.
import bmesh
ref = bpy.data.collections.new("Course_preview_only"); ref["role"] = "preview_only"
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


add(box("Surround_preview", 14.0, 7.0, 0.01, (3.0, 0, -0.0060)), "floor", mat("DarkConcrete_preview", (0.30, 0.31, 0.32), 0.8))
duck = add(box("Microduck_25cm_marker", 0.10, 0.14, 0.25, (0.25, 0, 0.125)), "marker", mat("Marker_yellow", (1.0, 0.55, 0.02), 0.4))
bev = duck.modifiers.new("Bevel", "BEVEL"); bev.width = 0.02; bev.segments = 4; bev.affect = "EDGES"
sun_d = bpy.data.lights.new("Sun_preview", "SUN"); sun_d.energy = 3.4; sun_d.angle = math.radians(3)
sun = add(bpy.data.objects.new("Sun_preview", sun_d), "sun"); sun.rotation_euler = (math.radians(62), 0, math.radians(-140))
w = bpy.data.worlds.new("Course_world"); sc.world = w; w.use_nodes = True; wn = w.node_tree
coord = wn.nodes.new("ShaderNodeTexCoord"); sep = wn.nodes.new("ShaderNodeSeparateXYZ"); ramp = wn.nodes.new("ShaderNodeValToRGB")
wn.links.new(coord.outputs["Generated"], sep.inputs[0]); wn.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.92, 0.93, 0.95, 1)
ramp.color_ramp.elements[1].position = 0.4; ramp.color_ramp.elements[1].color = (0.25, 0.42, 0.75, 1)
wn.links.new(ramp.outputs["Color"], wn.nodes["Background"].inputs["Color"])
wn.nodes["Background"].inputs["Strength"].default_value = 0.8
sc.camera = camera("Cam_overview", "camera", (-1.5, -2.9, 2.3), (3.0, 0.0, 0.0), 28)
for i, (loc, tgt) in enumerate([((0.25, 0.0, 0.20), (1.30, 0.0, 0.02)),      # start line, facing the hump
                                ((1.95, -0.15, 0.20), (2.80, 0.0, 0.0)),     # after the hump, facing the steps
                                ((3.55, 0.10, 0.20), (4.30, 0.0, 0.0)),      # after the steps, facing the wet floor
                                ((4.70, 0.0, 0.20), (5.20, 0.15, 0.05))], 1):  # past the wet floor, facing the box
    camera(f"Cam_duck_eye_{i}", f"camera_eye_{i}", loc, tgt, 24)
with ctx():
    bpy.ops.object.select_all(action="DESELECT")
    area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.view3d.view_center_camera()
print("staged", sorted(o.name for o in ref.objects))
