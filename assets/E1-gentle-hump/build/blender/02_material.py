# E1 gentle hump, Blender step 2/5: box-projected UVs in metres + the shared BirchPlywood material.
# Vars: SCENE, TEX (absolute path of assets/_materials/birch-plywood/basecolor.png).
ob = tagged("asset"); me = ob.data
img = bpy.data.images.load(TEX, check_existing=True)
uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
for p in me.polygons:                     # top faces use (x, y), side faces (x, z) or (y, z); 1 UV unit = 1 m
    nx, ny, nz = (abs(c) for c in p.normal)
    for li in p.loop_indices:
        x, y, z = me.vertices[me.loops[li].vertex_index].co
        uv.data[li].uv = (x, y + 0.3) if nz >= max(nx, ny) else ((x, z) if ny >= nx else (y + 0.3, z))
mat = bpy.data.materials.get("BirchPlywood") or bpy.data.materials.new("BirchPlywood")
mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
tex = nt.nodes.new("ShaderNodeTexImage"); tex.location = (-350, 0); tex.image = img
bsdf.inputs["Roughness"].default_value = 0.55
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"]); nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
me.materials.clear(); me.materials.append(mat)
area.spaces.active.shading.type = "MATERIAL"
print("material", mat.name, "texture", img.filepath, img.size[:], "uv loops", len(uv.data))
