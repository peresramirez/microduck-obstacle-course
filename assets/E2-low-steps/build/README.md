# E2 build scripts

Everything needed to rebuild E2 (low steps) from nothing, exactly as the files in `../` were made.

## Rebuild

1. Open **FreeCAD 1.1.x** (its MCP add-on starts the RPC server on port 9875 by itself) and **Blender 5.2.x** (N-panel → *MCP for Blender* → *Connect*, port 9876). Setup: `../../../../SETUP.md` sections 5–6.
2. From `isaac-obstacle-course/`:

```bash
assets/E2-low-steps/build/build.sh                                       # overwrites assets/E2-low-steps/
OUT=/tmp/e2 DOC=E2_test SCENE=E2_test assets/E2-low-steps/build/build.sh  # somewhere else, other names
RECORD=02-2-e2-rebuild assets/E2-low-steps/build/build.sh                # also records videos/<RECORD>-{freecad,blender}.mp4
```

About 1 minute, $0, ends with `tools/check_asset.py` (13 checks, including each sheet's position).

Verified 2026-10-26: a rebuild into a scratch folder gave pixel-identical `preview.png` and `preview-detail.png` (SSIM 1.000), identical STEP geometry (only the assembly-occurrence ID counter differs) and 13/13 checks.

## What runs, in order

| Step | Script | App | Does |
|---|---|---|---|
| 1 | `freecad/01_params.py` | FreeCAD | New document, `Params`: `rise` 10, `tread` 200, `top_length` 800, `width` 600 mm; `bottom_length = top_length + 2 * tread` |
| 2 | `freecad/02_sheets.py` | FreeCAD | `App::Part` `E2_LowSteps` with two `Part::Box` sheets; all sizes and placements are expressions over `Params` |
| 2b | `freecad/02b_demo_rise.py` | FreeCAD | On-camera demo: rise 15 → 5 → 10 mm (back to spec) |
| 3 | `freecad/03_export.py` | FreeCAD | Saves `model.FCStd`, exports `model.step` + one STL per sheet, reads the STEP back |
| — | `../../_materials/birch-plywood/make_texture.py`, `make_edge_texture.py` | Blender | Only if `basecolor.png` / `edge.png` are missing |
| 4 | `blender/01_import.py` | Blender | New scene, imports both STLs at 0.001, bakes the scale into the vertices |
| 5 | `blender/02_material.py` | Blender | Face veneer on up/down faces, ply edge on the sides; UVs in metres (edge v = z / 0.010) |
| 6 | `blender/03_stage.py` | Blender | Preview-only collection: floor, 25 cm marker + label, sun, wide + close-up cameras |
| 7 | `blender/04_render.py` | Blender | `preview.png`, `preview-detail.png` |
| 8 | `blender/05_export.py` | Blender | `model.usd` (+ `textures/`), `model.glb`, `model.blend` |

`blender/_common.py` is sent in front of every Blender step. Scripts take `DOC`, `SCENE`, `OUT`, `TEX`, `EDGE_TEX`, `RISE` through `tools/apps.py exec … --var NAME=VALUE`.
