# Course floor textures for F, generated in Blender (numpy). Deterministic (seed 31).
# One image pair covers the whole 6.0 x 1.2 m lane (4096 x 820 px, ~1.46 mm/px): UV = (x / 6.0, (y + 0.6) / 1.2).
#   basecolor.png  polished light-grey concrete (soft mottling, fine aggregate) + white tape lines across the lane
#   roughness.png  polished concrete 0.22-0.38 (mottled), tape 0.6 (matte)
# Tape positions come in as variables so they follow layout.json: START_X, FINISH_X, TAPE_W (metres, centre of each line).
# Run: uv run --no-project python tools/apps.py exec blender assets/_materials/polished-concrete/make_textures.py \
#        --var DIR=$PWD/assets/_materials/polished-concrete --var START_X=0.40 --var FINISH_X=5.60 --var TAPE_W=0.05
import os
import bpy, numpy as np

W, H, LX, LY = 4096, 820, 6.0, 1.2
sx, fx, tw = float(START_X), float(FINISH_X), float(TAPE_W)
rng = np.random.default_rng(31)
x, y = np.meshgrid(np.linspace(0, LX, W, endpoint=False), np.linspace(0, LY, H, endpoint=False))
# concrete: low-frequency clouds + fine aggregate speckle (a trowel-swirl term drew visible rings; removed)
clouds = sum(a * np.sin(2 * np.pi * (fx_ * x + fy_ * y + ph)) for a, fx_, fy_, ph in
             zip(rng.uniform(0.005, 0.015, 8), rng.uniform(0.1, 1.5, 8), rng.uniform(0.2, 2.0, 8), rng.uniform(0, 1, 8)))
speckle = rng.normal(0, 0.018, (H, W)) * (rng.random((H, W)) < 0.25)
grey = 0.70 + clouds + speckle
rgb = np.stack([grey, grey, grey * 0.985 + 0.004], -1)
rough = np.clip(0.30 + 2.5 * clouds + 0.4 * speckle, 0.22, 0.38)
# tape: 5 cm white strips across the whole width, edges wobble ~0.5 mm, a few tiny wrinkles
tape = np.zeros((H, W), bool)
for cx in (sx, fx):
    wob = 0.0005 * np.sin(2 * np.pi * (y * rng.uniform(3, 9) + rng.uniform()))
    tape |= np.abs(x - cx - wob) < tw / 2
tape_tone = 0.93 + rng.normal(0, 0.006, (H, W)) - 0.02 * (np.sin(2 * np.pi * y * 40) > 0.97)
rgb = np.where(tape[..., None], np.stack([tape_tone] * 3, -1), rgb)
rough = np.where(tape, 0.6, rough)
os.makedirs(DIR, exist_ok=True)
for name, arr, cs in (("basecolor.png", np.clip(rgb, 0, 1), "sRGB"), ("roughness.png", np.repeat(rough[..., None], 3, -1), "Non-Color")):
    img = bpy.data.images.new("tmp_" + name, W, H)
    img.colorspace_settings.name = cs
    img.pixels.foreach_set(np.dstack([arr, np.ones((H, W, 1))])[::-1].astype(np.float32).ravel())
    img.filepath_raw = os.path.join(DIR, name); img.file_format = "PNG"; img.save(); bpy.data.images.remove(img)
print("floor textures", DIR, "tape at x", sx, fx, "width", tw, "tape px", int(tape.sum() // H))
