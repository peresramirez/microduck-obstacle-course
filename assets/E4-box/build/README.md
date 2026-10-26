# E4 build scripts

Everything needed to rebuild E4 (box) from nothing, exactly as the files in `../` were made.

## Rebuild

1. Open **FreeCAD 1.1.x** (MCP RPC on port 9875 starts by itself) and **Blender 5.2.x** (N-panel → *MCP for Blender* → *Connect*, port 9876). Setup: `../../../../SETUP.md` sections 5–6.
2. From `isaac-obstacle-course/`:

```bash
assets/E4-box/build/build.sh                                  # overwrites assets/E4-box/
OUT=/tmp/e4 DOC=E4_test SCENE=E4_test assets/E4-box/build/build.sh   # somewhere else, other names
RECORD=02-4-e4-rebuild assets/E4-box/build/build.sh           # also records videos/<RECORD>-{freecad,blender}.mp4
```

About 1–2 minutes, $0, ends with `tools/check_asset.py` (11 checks). Verified 2026-10-26: scratch rebuild → both previews SSIM 1.000, STEP geometry identical, 11/11.

## What runs, in order

| Step | Script | App | Does |
|---|---|---|---|
| 1 | `freecad/01_params.py` | FreeCAD | New document, `Params`: `length`/`width` 200, `height` 150, `wall` 12, `hole_length` 90, `hole_height` 30, `hole_top_offset` 30 mm; `friction` 0.8 (reference) |
| 2 | `freecad/02_box.py` | FreeCAD | `Shell` = `Outer` − `Inner`; hand-hole cutter = box + 2 cylinders; `Box` = `Shell` − cutter. All expressions |
| 2b | `freecad/02b_demo_height.py` | FreeCAD | On-camera demo: height 100 → 200 → 150 mm (back to spec) |
| 3 | `freecad/03_export.py` | FreeCAD | Saves `model.FCStd`, exports `model.step` (final `Box`) + `freecad-mesh.stl`, reads the STEP back |
| — | `../../_materials/birch-plywood/make_texture.py`, `make_edge_texture.py` | Blender | Only if the textures are missing |
| 4 | `blender/01_import.py` | Blender | New scene, imports at 0.001, bakes the scale, smooth by angle (30°) |
| 5 | `blender/02_material.py` | Blender | Face veneer everywhere, ply edge on the hand-hole's cut faces (found inside the 12 mm −y wall) |
| 6 | `blender/03_stage.py` | Blender | Preview-only: floor, 25 cm marker beside the box, sun, wide + close-up cameras |
| 7 | `blender/04_render.py` | Blender | `preview.png`, `preview-detail.png` (Eevee with ray tracing, so the box's inside stays dark) |
| 8 | `blender/05_export.py` | Blender | `model.usd` (+ `textures/`), `model.glb`, `model.blend`; tags friction 0.8, collider box |

Variables: `DOC`, `SCENE`, `OUT`, `TEX`, `EDGE_TEX`, `HEIGHT`.
