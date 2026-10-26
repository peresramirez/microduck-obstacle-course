# E2 low steps, Blender step 2/5: two materials per sheet, UVs in metres.
#   faces pointing up/down -> BirchPlywood (face veneer, shared with E1), UV (x, y)
#   cut edges (sides)      -> BirchPlywoodEdge (7 plies), UV (along-edge, z / SHEET) so the ply pattern repeats once per sheet
# Vars: SCENE, TEX (face texture), EDGE_TEX (edge texture), both absolute paths.
SHEET = 0.010   # spec sheet thickness = rise (m)


def image_material(name, path, rough):
    img = bpy.data.images.load(path, check_existing=True)
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.location = (-350, 0); tex.image = img
    bsdf.inputs["Roughness"].default_value = rough
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"]); nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


face = image_material("BirchPlywood", TEX, 0.55)
edge = image_material("BirchPlywoodEdge", EDGE_TEX, 0.65)
for ob in assets():
    me = ob.data
    me.materials.clear(); me.materials.append(face); me.materials.append(edge)
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        nx, ny, nz = (abs(c) for c in p.normal)
        p.material_index = 0 if nz >= max(nx, ny) else 1
        for li in p.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (x, y + 0.3) if p.material_index == 0 else ((x, z / SHEET) if ny >= nx else (y + 0.3, z / SHEET))
    print(ob.name, "faces top/bottom", sum(p.material_index == 0 for p in me.polygons), "edge", sum(p.material_index == 1 for p in me.polygons))
area.spaces.active.shading.type = "MATERIAL"
