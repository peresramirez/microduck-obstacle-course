# E3 build scripts

Everything needed to rebuild E3 (wet floor) from nothing, exactly as the files in `../` were made.

## Rebuild

1. Open **FreeCAD 1.1.x** (MCP RPC on port 9875 starts by itself) and **Blender 5.2.x** (N-panel → *MCP for Blender* → *Connect*, port 9876). Setup: `../../../../SETUP.md` sections 5–6.
2. From `isaac-obstacle-course/`:

```bash
assets/E3-wet-floor/build/build.sh                                       # overwrites assets/E3-wet-floor/
OUT=/tmp/e3 DOC=E3_test SCENE=E3_test assets/E3-wet-floor/build/build.sh  # somewhere else, other names
RECORD=02-3-e3-rebuild assets/E3-wet-floor/build/build.sh                # also records videos/<RECORD>-{freecad,blender}.mp4
```

About 1 minute, $0, ends with `tools/check_asset.py` (12 checks). Verified 2026-10-26: scratch rebuild → both previews SSIM 1.000, STEP geometry identical, 12/12.

## What runs, in order

| Step | Script | App | Does |
|---|---|---|---|
| 1 | `freecad/01_params.py` | FreeCAD | New document, `Params`: `length` 800, `width` 600, `thickness` 2 mm, `friction` 0.3 (reference only) |
| 2 | `freecad/02_tile.py` | FreeCAD | `Part::Box` tile bound to `Params`, inside `App::Part` `E3_WetFloor` (keeps the placement in STEP) |
| 3 | `freecad/03_export.py` | FreeCAD | Saves `model.FCStd`, exports `model.step` + `freecad-mesh.stl`, reads the STEP back |
| — | `../../_materials/wet-tile/make_textures.py` | Blender | Only if the textures are missing: base colour + roughness (seed 21) |
| 4 | `blender/01_import.py` | Blender | New scene, imports the STL at 0.001, bakes the scale |
| 5 | `blender/02_material.py` | Blender | `WetTile` material: base colour + roughness images, UV over the whole tile |
| 6 | `blender/03_stage.py` | Blender | Preview-only: dark concrete floor, 25 cm marker, sun, sky-gradient world (gives the puddles something to reflect), wide + low cameras |
| 7 | `blender/04_render.py` | Blender | `preview.png`, `preview-detail.png` (Eevee with screen-space raytracing) |
| 8 | `blender/05_export.py` | Blender | `model.usd` (+ `textures/`), `model.glb`, `model.blend`; tags friction 0.3 |

Variables: `DOC`, `SCENE`, `OUT`, `BASE_TEX`, `ROUGH_TEX` (`tools/apps.py exec … --var NAME=VALUE`).
