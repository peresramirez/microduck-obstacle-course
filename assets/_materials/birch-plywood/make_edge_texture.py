# Birch plywood cut edge: 7 plies across one 10 mm sheet, generated in Blender (numpy). Shared by E2 and E4.
# 2048 x 512 px; u covers 1 m along the edge, v covers one sheet thickness (UV v = z / sheet_thickness, so it
# repeats once per sheet). Plies alternate long grain (light streaks) and cross grain (darker, end-grain flecks),
# separated by thin glue lines. Deterministic (seed 12).
# Run: uv run --no-project python tools/apps.py exec blender assets/_materials/birch-plywood/make_edge_texture.py --var TEX=$PWD/assets/_materials/birch-plywood/edge.png
import bpy, numpy as np

w, h, plies = 2048, 512, 7
rng = np.random.default_rng(12)
u, v = np.meshgrid(np.linspace(0, 1, w, endpoint=False), np.linspace(0, 1, h, endpoint=False))
ply = np.minimum((v * plies).astype(int), plies - 1)
local = v * plies - ply                                   # 0..1 inside each ply
long_grain = (ply % 2 == 0)                               # outer plies (0 and 6) run along the face
streak = sum(np.sin(2 * np.pi * (rng.uniform(40, 160) * v + rng.uniform() + 0.3 * np.sin(2 * np.pi * rng.uniform(1, 4) * u)))
             for _ in range(4)) / 4
fleck = (np.sin(2 * np.pi * (u * rng.uniform(300, 500))) * np.sin(2 * np.pi * (v * 90 + rng.uniform()))) > 0.75
t = np.where(long_grain, 0.10 + 0.08 * streak, 0.28 + 0.10 * streak + 0.18 * fleck)
glue = np.exp(-((np.minimum(local, 1 - local)) / 0.035) ** 2)   # thin dark line at every ply boundary
t = np.clip(t + 0.55 * glue * (ply > 0) * (local < 0.5) + 0.55 * glue * (ply < plies - 1) * (local >= 0.5), 0, 1)[..., None]
light, dark = np.array([0.93, 0.86, 0.73]), np.array([0.55, 0.42, 0.27])   # sRGB, written as-is
rgb = np.clip(light + (dark - light) * t, 0, 1)
img = bpy.data.images.new("tmp_birch_edge", w, h)
img.pixels.foreach_set(np.dstack([rgb, np.ones((h, w, 1))])[::-1].astype(np.float32).ravel())
img.filepath_raw = TEX; img.file_format = "PNG"; img.save(); bpy.data.images.remove(img)
print("edge texture", TEX)
