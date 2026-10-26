# Birch plywood base colour, generated in Blender (numpy). Shared by E1, E2 and E4.
# 2048 px covers 1 m x 1 m; grain runs along x (the lane). Deterministic (seed 11).
# Run: uv run --no-project python tools/apps.py exec blender assets/_materials/birch-plywood/make_texture.py --var TEX=$PWD/assets/_materials/birch-plywood/basecolor.png
import bpy, numpy as np

n = 2048; rng = np.random.default_rng(11)
u, v = np.meshgrid(np.linspace(0, 1, n, endpoint=False), np.linspace(0, 1, n, endpoint=False))
# grain lines run along x (u); spacing and drift vary slowly so it reads as rotary-cut birch veneer
drift = sum(a * np.sin(2 * np.pi * (f * u + g * v + rng.uniform())) for a, f, g in
            [(1.2, 1, 0.2), (0.7, 2, 0.5), (0.35, 3, 1.3), (0.15, 1, 4.0)])
phase = 70 * v + drift + 6 * np.sin(2 * np.pi * (0.7 * v + rng.uniform()))
line = (0.5 + 0.5 * np.cos(2 * np.pi * phase)) ** 10
fine = sum(np.sin(2 * np.pi * (rng.uniform(250, 600) * v + 3 * drift / 70 + rng.uniform())) for _ in range(5)) / 5
patch = sum(np.sin(2 * np.pi * (a * u + b * v + c)) for a, b, c in rng.uniform(0.3, 2.5, (5, 3))) / 5
t = np.clip(0.30 * line + 0.06 * fine + 0.10 * patch + 0.12, 0, 1)[..., None]
light, dark = np.array([0.93, 0.86, 0.73]), np.array([0.78, 0.65, 0.47])   # sRGB, written as-is (no gamma)
rgb = np.clip(light + (dark - light) * t, 0, 1)
img = bpy.data.images.new("tmp_birch", n, n)
img.pixels.foreach_set(np.dstack([rgb, np.ones((n, n, 1))])[::-1].astype(np.float32).ravel())
img.filepath_raw = TEX; img.file_format = "PNG"; img.save(); bpy.data.images.remove(img)
print("texture", TEX)
