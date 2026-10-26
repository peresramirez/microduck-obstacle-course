# E4 box, Blender step 2/5: BirchPlywood (face veneer) everywhere, BirchPlywoodEdge (7 plies) on the hand-hole's cut
# surfaces, i.e. the faces lying inside the 12 mm thickness of the -y wall. UVs in metres.
# Vars: SCENE, TEX (face texture), EDGE_TEX (edge texture), both absolute paths.
WALL, HALF_W = 0.012, 0.100      # spec wall thickness and half width (m)


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
ob = tagged("asset"); me = ob.data
me.materials.clear(); me.materials.append(face); me.materials.append(edge)
uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
n_edge = 0
for p in me.polygons:
    cy = p.center.y
    in_wall = -HALF_W + 1e-5 < cy < -HALF_W + WALL - 1e-5        # strictly inside the -y wall = hand-hole cut
    p.material_index = 1 if in_wall and abs(p.normal.y) < 0.5 else 0
    n_edge += p.material_index
    nx, ny, nz = (abs(c) for c in p.normal)
    for li in p.loop_indices:
        x, y, z = me.vertices[me.loops[li].vertex_index].co
        if p.material_index == 1:
            uv.data[li].uv = (x + z, (y + HALF_W) / WALL)           # plies stacked through the wall thickness
        else:
            uv.data[li].uv = (x, y + HALF_W) if nz >= max(nx, ny) else ((x, z) if ny >= nx else (y + HALF_W, z))
area.spaces.active.shading.type = "MATERIAL"
print(ob.name, "triangles: face veneer", len(me.polygons) - n_edge, "ply edge (hand-hole)", n_edge)
