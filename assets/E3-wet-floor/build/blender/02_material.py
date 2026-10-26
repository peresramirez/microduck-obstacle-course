# E3 wet floor, Blender step 2/5: WetTile material = base colour + roughness images (puddles darker and near-mirror).
# UV maps the whole tile once: (x / 0.8, (y + 0.3) / 0.6). Water is visual only; physics is low friction.
# Vars: SCENE, BASE_TEX, ROUGH_TEX (absolute paths).
LX, LY = 0.8, 0.6
ob = tagged("asset"); me = ob.data
mat = bpy.data.materials.get("WetTile") or bpy.data.materials.new("WetTile")
mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (0, 0)
base = nt.nodes.new("ShaderNodeTexImage"); base.location = (-400, 150); base.image = bpy.data.images.load(BASE_TEX, check_existing=True)
rough = nt.nodes.new("ShaderNodeTexImage"); rough.location = (-400, -200); rough.image = bpy.data.images.load(ROUGH_TEX, check_existing=True)
rough.image.colorspace_settings.name = "Non-Color"
nt.links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
me.materials.clear(); me.materials.append(mat)
uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
for p in me.polygons:
    for li in p.loop_indices:
        x, y, z = me.vertices[me.loops[li].vertex_index].co
        uv.data[li].uv = (x / LX, (y + LY / 2) / LY)        # 2 mm sides just take the colour at their edge
area.spaces.active.shading.type = "MATERIAL"
print("material", mat.name, "base", base.image.size[:], "roughness", rough.image.size[:], rough.image.colorspace_settings.name)
