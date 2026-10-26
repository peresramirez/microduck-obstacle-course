# Birch plywood material (shared)

Used by E1 (gentle hump), E2 (low steps) and E4 (box).

- `basecolor.png`: 2048 × 2048 sRGB, covers 1 m × 1 m, grain along x. Made by `make_texture.py` (runs inside Blender, numpy, seed 11, so it comes out identical every time).
- `edge.png`: 2048 × 512 sRGB, the cut edge of a 10 mm sheet: 7 plies (alternating long grain and cross grain, glue lines). u = 1 m along the edge, v = one sheet thickness (UV v = z / 0.010, repeats per sheet). Made by `make_edge_texture.py` (seed 12). Used by E2 (and E4).
- Blender material `BirchPlywoodEdge`: Principled BSDF, Base Color = `edge.png`, Roughness 0.65, on faces that aren't pointing up or down.
- Blender material `BirchPlywood`: Principled BSDF, Base Color = this image, Roughness 0.55. UVs are in metres (1 UV unit = 1 m), so the grain has the same real-world size on every asset.
- Physics: friction 1.0.

Rebuild: `uv run --no-project python tools/apps.py exec blender assets/_materials/birch-plywood/make_edge_texture.py --var TEX=$PWD/assets/_materials/birch-plywood/edge.png` and `uv run --no-project python tools/apps.py exec blender assets/_materials/birch-plywood/make_texture.py --var TEX=$PWD/assets/_materials/birch-plywood/basecolor.png` (from `isaac-obstacle-course/`, Blender open with its MCP add-on connected).
