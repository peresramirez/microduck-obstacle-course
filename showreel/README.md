# Showreels

Edited videos of the pipeline, built from the app recordings in `../videos/` (git-ignored; on disk only).

| Sequence | Output | Length | What |
|---|---|---|---|
| `phase2.json` | `videos/phase-2-assets/showreel-phase2.mp4` | ~11.5 min | Phase 2: the five assets in FreeCAD and Blender, the bug caught in E3 take 1, the assembled course, duck-eye views, the fly-through, the scripted rebuild |

## Build

From `isaac-obstacle-course/`:

```bash
uv run --no-project python tools/make_showreel.py showreel/phase2.json
```

Edit the JSON to reorder, retime (`seconds` for cards/stills, `speed` for clips) or relabel; then rebuild. Every segment is normalised to 1920 × 1080, 30 fps, H.264, no audio; app clips (1920 × 1056/1060) are padded, the 1280 × 720 fly-through is scaled up. Title cards and labels are HTML captured by headless Chrome (labels with a transparent background, overlaid bottom-left; the label shows the playback speed when it isn't 1×). Work files go to `build/<sequence>/` (git-ignored, regenerated).

There's no sound: add music or narration in an editor, or ask Claude to use the HyperFrames video skill for animated titles and audio.
