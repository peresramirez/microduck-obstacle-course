# Wet floor tile textures for E3, generated in Blender (numpy). Deterministic (seed 21).
# One image pair covers the whole 0.8 x 0.6 m tile (2048 x 1536 px, 2.56 px/mm): UV = (x / 0.8, (y + 0.3) / 0.6).
#   basecolor.png  light-grey ceramic tiles (0.2 m grid, 3 mm grout), darker where wet
#   roughness.png  dry tile 0.35, grout 0.75, puddles 0.03 (near mirror) -> the water is visual only
# Run: uv run --no-project python tools/apps.py exec blender assets/_materials/wet-tile/make_textures.py --var DIR=$PWD/assets/_materials/wet-tile
import os
import bpy, numpy as np

W, H, LX, LY = 2048, 1536, 0.8, 0.6
rng = np.random.default_rng(21)
x, y = np.meshgrid(np.linspace(0, LX, W, endpoint=False), np.linspace(0, LY, H, endpoint=False))
# tiles and grout
gx, gy = np.mod(x, 0.2), np.mod(y, 0.2)
grout = (np.minimum(gx, 0.2 - gx) < 0.0015) | (np.minimum(gy, 0.2 - gy) < 0.0015)
tile_id = (x // 0.2).astype(int) * 7 + (y // 0.2).astype(int)
tone = rng.uniform(-0.025, 0.025, tile_id.max() + 1)[tile_id]
speckle = rng.normal(0, 0.012, (H, W))
# puddles: a few elongated blobs, edges wobbled by low-frequency noise
field = np.zeros((H, W))
for cx, cy, rx, ry in [(0.22, 0.38, 0.13, 0.08), (0.50, 0.20, 0.10, 0.07), (0.62, 0.42, 0.08, 0.06), (0.36, 0.14, 0.05, 0.04)]:
    field += np.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))
wobble = sum(0.08 * np.sin(2 * np.pi * (a * x / LX + b * y / LY + c)) for a, b, c in rng.uniform(1, 6, (6, 3)))
wet = np.clip(((field + wobble) - 0.45) / 0.10, 0, 1)        # soft 0..1 edge
film = np.clip(field * 1.6, 0, 1) * 0.35                      # thin damp halo around puddles
dampness = np.maximum(wet, film)
base = np.where(grout, 0.56, 0.82 + tone) + speckle
rgb = np.stack([base, base + 0.005, base + 0.012], -1)       # very slightly cool grey
rgb = rgb * (1 - 0.30 * dampness[..., None])                  # wet surfaces look darker
rgb[..., 2] += 0.025 * dampness                               # and slightly cooler (thin water film)
rough = np.where(grout, 0.75, 0.35)
rough = rough * (1 - dampness) + 0.03 * dampness
os.makedirs(DIR, exist_ok=True)
for name, arr, cs in (("basecolor.png", np.clip(rgb, 0, 1), "sRGB"), ("roughness.png", np.repeat(rough[..., None], 3, -1), "Non-Color")):
    img = bpy.data.images.new("tmp_" + name, W, H)
    img.colorspace_settings.name = cs
    img.pixels.foreach_set(np.dstack([arr, np.ones((H, W, 1))])[::-1].astype(np.float32).ravel())
    img.filepath_raw = os.path.join(DIR, name); img.file_format = "PNG"; img.save(); bpy.data.images.remove(img)
print("wet tile textures", DIR, "wet area %.0f%%" % (100 * (wet > 0.5).mean()))
