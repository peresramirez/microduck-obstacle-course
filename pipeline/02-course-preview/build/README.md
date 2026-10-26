# Course preview build scripts

Rebuild the whole-course preview from the five exported assets.

1. Build the assets first (each `assets/<id>/build/build.sh`), then open **Blender 5.2.x** with *MCP for Blender* connected (port 9876).
2. From `isaac-obstacle-course/`:

```bash
pipeline/02-course-preview/build/build.sh                          # checks, stills, fly-through (~3 min for the fly-through)
OUT=/tmp/course SCENE=Course_test ANIM=0 pipeline/02-course-preview/build/build.sh   # elsewhere, stills only (~2 min)
```

| Step | Script | Does |
|---|---|---|
| 0 | `tools/check_course.py` | 17 course-level checks from the exported USDs at their layout positions |
| 1 | `blender/01_assemble.py` | New scene; imports F, E1–E4 `model.usd` (textures referenced, `IMPORT_NONE`) and places them from `layout.json` |
| 2 | `blender/02_stage.py` | Preview-only: surround, sun, sky-gradient world, 25 cm marker, overview + 4 duck-eye cameras |
| 3 | `blender/03_render_stills.py` | `renders/overview.png`, `renders/duck-eye-1..4.png` |
| 4 | `blender/04_flythrough.py` | Keyframes the marker along the smoothed route + chase camera; saves `course.blend` |
| 5 | background `Blender -b course.blend -S Course_preview -a` + ffmpeg | `renders/flythrough/*.png` → `videos/phase-2-assets/02-6-course-flythrough.mp4` |

`blender/_common.py` (sent in front of every step) also has `placements(layout)`, the single place where layout.json corners become asset origins.
