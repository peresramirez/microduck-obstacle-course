# F build scripts

Everything needed to rebuild F (floor and lane) from nothing, exactly as the files in `../` were made.

## Rebuild

1. Open **FreeCAD 1.1.x** (MCP RPC on port 9875 starts by itself) and **Blender 5.2.x** (N-panel → *MCP for Blender* → *Connect*, port 9876). Setup: `../../../../SETUP.md` sections 5–6.
2. From `isaac-obstacle-course/`:

```bash
assets/F-floor/build/build.sh                                 # overwrites assets/F-floor/
OUT=/tmp/f DOC=F_test SCENE=F_test assets/F-floor/build/build.sh   # somewhere else, other names
RECORD=02-5-f-rebuild assets/F-floor/build/build.sh           # also records videos/<RECORD>-{freecad,blender}.mp4
```

About 1 minute, $0, ends with `tools/check_asset.py` (12 checks). Verified 2026-10-26: scratch rebuild → both previews SSIM 1.000, STEP geometry identical, 12/12.

## What runs, in order

| Step | Script | App | Does |
|---|---|---|---|
| 1 | `freecad/01_params.py` | FreeCAD | New document, `Params`: 6000 × 1200 mm, tape at 400 / 5600 mm, 50 mm wide; `friction` 1.0 (reference) |
| 2 | `freecad/02_floor.py` | FreeCAD | `Part::Plane` floor at z = 0 in `App::Part` `F_Floor`; view-only tape rectangles |
| 3 | `freecad/03_export.py` | FreeCAD | Saves `model.FCStd`, exports `model.step` + `freecad-mesh.stl`, reads the STEP back |
| — | `../../_materials/polished-concrete/make_textures.py` | Blender | Only if the textures are missing: concrete + tape at `START_X` 0.40, `FINISH_X` 5.60, `TAPE_W` 0.05 |
| 4 | `blender/01_import.py` | Blender | New scene, imports at 0.001, bakes the scale, makes sure the face points up |
| 5 | `blender/02_material.py` | Blender | `PolishedConcrete`: base colour + roughness, UV over the whole lane |
| 6 | `blender/03_stage.py` | Blender | Preview-only: darker surround, marker in the start area, sun, sky-gradient world, 3/4 wide camera + start-line camera |
| 7 | `blender/04_render.py` | Blender | `preview.png`, `preview-detail.png` |
| 8 | `blender/05_export.py` | Blender | `model.usd` (+ `textures/`), `model.glb`, `model.blend`; tags ground plane, friction 1.0 |

Variables: `DOC`, `SCENE`, `OUT`, `BASE_TEX`, `ROUGH_TEX`.
