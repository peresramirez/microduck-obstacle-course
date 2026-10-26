"""Render the course plan as a presentation page: docs/plan.html.

Sources: pipeline/01-plan/plan.md and robot-specs.md (full text), layout.json (map and
true-scale profiles), concept/*.png (FLUX visuals), video-reference/*.png (NVIDIA frames).

Run from isaac-obstacle-course/:  uv run --no-project --with markdown python tools/render_plan.py
"""

import json
import math
from html import escape
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
PLAN_DIR = ROOT / "pipeline/01-plan"
OUT = ROOT / "docs/plan.html"
REL = "../pipeline/01-plan"  # image paths as seen from docs/

STAGES = [
    ("1", "Plan the course", "specs, course, visuals, asset list", "Mac", "now"),
    ("2", "Build assets", "FreeCAD → Blender → USD", "Mac", "next"),
    ("3", "Cloud workstation", "Nebius RTX PRO 6000, Isaac Sim streamed", "Nebius", ""),
    ("4", "Baseline walking", "stock Microduck task, 4,096 envs", "Nebius", ""),
    ("5", "Assemble the scene", "colliders, friction, 8×8 depth sensor", "Nebius", ""),
    ("6", "Train on the course", "randomised E1–E4 + depth grid", "Nebius", ""),
    ("7", "Validate", "several ducks, full course, videos", "Nebius", ""),
]

# One card per element: image, what it tests, trained range that makes it doable.
PARTS = {
    "E1": ("v2-e1-gentle-hump.png", "Balance going up and down a slope.",
           "Trained on slopes of 1.7°–5.7° (NVIDIA rough terrain); the Arena hill climb is 8°.",
           "1.0 m × 0.6 m · crest 3.3 cm · max slope 5.9° → training up to 4.4 cm / 8°"),
    "E2": ("v2-e2-low-steps.png", "Lifting the feet over step edges.",
           "Trained on stairs of 0–1.5 cm (NVIDIA rough terrain).",
           "Two stacked 1 cm plywood sheets: 1.2 m bottom, 0.8 m top · 2 cm at the highest → training up to 1.5 cm per step"),
    "E3": ("v2-e3-wet-floor.png", "Keeping balance when the feet slip.",
           "Not yet: the stock Isaac Lab policy only saw foot grip 0.7–1.3 on ground 1.0, so the wet floor is a training target (0.2–1.2).",
           "0.8 m × 0.6 m · grip μ 0.3 → training down to 0.2 · simulated as low friction, not liquid"),
    "E4": ("v2-e4-box.png", "Seeing an obstacle with the 8×8 depth sensor and walking around it.",
           "New skill (the reason for the depth input). The box is lower than the duck; 50 cm free on each side.",
           "20 × 20 × 15 cm box · lane widens to 1.2 m"),
}

COLORS = {"walk-on": "var(--wood)", "slippery": "var(--wet)", "obstacle": "var(--wood-dark)", "marker": "var(--accent)"}


def profile(item: dict, xs: list[float]) -> list[float]:
    """Height (m) of an element at local positions xs (m from its start)."""
    p, a = item.get("params", {}), item.get("asset")
    if a == "E1":
        return [p["crest"] / 2 * (1 - math.cos(2 * math.pi * x / p["length"])) for x in xs]
    if a == "E2":
        return [p["rise"] * (2 if p["tread"] <= x <= item["w"] - p["tread"] else 1) for x in xs]
    if a == "E3":
        return [p["thickness"] for _ in xs]
    if a == "E4":
        return [p["height"] for _ in xs]
    return [0.0 for _ in xs]


def duck(x_m: float, s: float, ground: float) -> str:
    """Microduck side silhouette at true scale: 25 cm tall, ~14 cm head, feet ~7 cm."""
    def r(x, z, w, h, cls="duck"):
        return f'<rect x="{(x_m + x) * s:.1f}" y="{ground - (z + h) * s:.1f}" width="{w * s:.1f}" height="{h * s:.1f}" rx="{0.01 * s:.1f}" class="{cls}"/>'
    return "".join([
        r(-0.035, 0.0, 0.07, 0.012, "duck-foot"),            # foot
        r(-0.012, 0.012, 0.024, 0.085),                       # leg
        r(-0.05, 0.095, 0.10, 0.055),                         # body
        r(-0.008, 0.15, 0.016, 0.045),                        # neck
        r(-0.05, 0.195, 0.14, 0.055),                         # head
        f'<circle cx="{(x_m + 0.085) * s:.1f}" cy="{ground - 0.222 * s:.1f}" r="{0.012 * s:.1f}" class="duck-eye"/>',
    ])


def part_profile_svg(item: dict) -> str:
    """True-scale side view of one element with the duck beside it (same scale both axes)."""
    pad_m, width_px = 0.25, 520
    span = item["w"] + 2 * pad_m
    s = width_px / span  # px per metre, both axes
    top_m = 0.30
    H = top_m * s + 26
    ground = top_m * s + 4
    n = 120
    xs = [i * item["w"] / n for i in range(n + 1)]
    zs = profile(item, xs)
    pts = [f"{(pad_m + x) * s:.1f},{ground - z * s:.1f}" for x, z in zip(xs, zs)]
    poly = f"{pad_m * s:.1f},{ground:.1f} " + " ".join(pts) + f" {(pad_m + item['w']) * s:.1f},{ground:.1f}"
    peak = max(zs)
    cls = item["kind"]
    return (
        f'<svg viewBox="0 0 {width_px} {H:.0f}" class="profile" role="img" aria-label="True-scale side view of {escape(item["label"])} with the duck">'
        f'<line x1="0" y1="{ground}" x2="{width_px}" y2="{ground}" class="ground"/>'
        f'<polygon points="{poly}" class="shape {cls}"/>'
        + duck(pad_m * 0.45, s, ground)
        + f'<text x="{width_px - 6}" y="{H - 8:.0f}" class="dim" text-anchor="end">'
          f'true scale · {item["w"]:.2f} m long · {peak * 100:.1f} cm high · duck 25 cm</text></svg>'
    )


def course_svg(layout: dict) -> str:
    """Top-down map of the whole lane."""
    s, pad = 180, 24
    W, D = layout["floor"]["w"], layout["floor"]["d"]
    out = [f'<svg viewBox="0 0 {W * s + 2 * pad} {D * s + 2 * pad + 26}" class="map" role="img" aria-label="Top-down course map">',
           f'<rect x="{pad}" y="{pad}" width="{W * s}" height="{D * s}" class="floor"/>']
    for i in range(1, int(W)):
        out.append(f'<line x1="{pad + i * s}" y1="{pad}" x2="{pad + i * s}" y2="{pad + D * s}" class="grid"/>')
    for it in layout["items"]:
        x, y, w, d = pad + it["x"] * s, pad + it["y"] * s, it["w"] * s, it["d"] * s
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" rx="3" fill="{COLORS[it["kind"]]}" class="item"/>')
        name = it.get("asset", it["label"])
        sub = it["label"] if "asset" in it else ""
        out.append(f'<text x="{x + w / 2:.1f}" y="{y + (16 if d > 40 else d / 2 + 4):.1f}" class="lbl">{escape(name)}</text>')
        if sub:
            out.append(f'<text x="{x + w / 2:.1f}" y="{y + d + 14:.1f}" class="lbl-sub">{escape(sub)}</text>')
    pts = " ".join(f"{pad + x * s},{pad + y * s}" for x, y in layout["route"])
    out.append(f'<polyline points="{pts}" class="route" marker-end="url(#arrow)"/>')
    by = pad + D * s + 16
    out.append(f'<line x1="{pad}" y1="{by}" x2="{pad + s}" y2="{by}" class="scale"/><text x="{pad + s / 2}" y="{by + 13}" class="lbl-sub">1 m</text>')
    out.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="arrowhead"/></marker></defs></svg>')
    return "\n".join(out)


def route_profile_svg(layout: dict) -> str:
    """True-scale side profile of the whole route (heights are real, so they look tiny)."""
    s, pad = 180, 24
    W = layout["floor"]["w"]
    ground = 70
    out = [f'<svg viewBox="0 0 {W * s + 2 * pad} 100" class="map" role="img" aria-label="Side profile of the route at true scale">',
           f'<line x1="{pad}" y1="{ground}" x2="{pad + W * s}" y2="{ground}" class="ground"/>']
    for it in layout["items"]:
        if it["kind"] == "marker":
            continue
        xs = [i * it["w"] / 60 for i in range(61)]
        zs = profile(it, xs)
        pts = " ".join(f"{pad + (it['x'] + x) * s:.1f},{ground - z * s:.1f}" for x, z in zip(xs, zs))
        out.append(f'<polygon points="{pad + it["x"] * s:.1f},{ground} {pts} {pad + (it["x"] + it["w"]) * s:.1f},{ground}" class="shape {it["kind"]}"/>')
        out.append(f'<text x="{pad + (it["x"] + it["w"] / 2) * s:.1f}" y="{ground + 16}" class="lbl-sub">{it["asset"]}</text>')
    out.append('<g transform="translate(0,0)">' + duck(0.25 + pad / s, s, ground) + "</g>")
    out.append(f'<text x="{pad + W * s}" y="94" class="dim" text-anchor="end">side view, true scale: the duck is 25 cm; the tallest element is the 15 cm box</text></svg>')
    return "\n".join(out)


def depth_grid_svg() -> str:
    """Illustration of the 8×8 ToF depth grid looking at the box ahead (not sensor data)."""
    cells, size = [], 34
    for r in range(8):
        for c in range(8):
            d = 0.35 + (7 - r) * 0.22  # floor: nearer at the bottom rows
            if 2 <= c <= 5 and 2 <= r <= 6:
                d = 0.55  # the box ahead
            if r < 2:
                d = 2.5  # far background
            shade = int(250 - min(d, 2.5) / 2.5 * 210)
            cells.append(f'<rect x="{c * size}" y="{r * size}" width="{size - 2}" height="{size - 2}" fill="rgb({shade},{shade},{shade})"><title>{d:.2f} m</title></rect>')
    box = (f'<rect x="{2 * size - 2}" y="{2 * size - 2}" width="{4 * size + 2}" height="{5 * size + 2}" class="box-outline"/>'
           f'<text x="{4 * size}" y="{2 * size + 16}" class="box-lbl">box 0.55 m</text>')
    return (f'<svg viewBox="-3 -3 {8 * size + 4} {8 * size + 4}" class="grid8" role="img" aria-label="8 by 8 depth grid illustration">'
            + "".join(cells) + box + "</svg>")


def img(path: str, caption: str) -> str:
    return (f'<figure><img src="{REL}/{path}" alt="{escape(caption)}" loading="lazy">'
            f"<figcaption>{caption}</figcaption></figure>")


def main() -> None:
    layout = json.loads((PLAN_DIR / "layout.json").read_text())
    items = {it["id"]: it for it in layout["items"]}
    md = lambda name: markdown.markdown((PLAN_DIR / name).read_text(), extensions=["tables", "fenced_code"])
    frames = "\n".join(img(f"video-reference/{p.name}", p.stem.replace("-", " ", 1).replace("-", " "))
                       for p in sorted((PLAN_DIR / "video-reference").glob("*.png")))
    stages = "\n".join(f'<li class="{st}"><span class="n">{n}</span><b>{t}</b><span>{d}</span><em>{w}</em></li>'
                       for n, t, d, w, st in STAGES)
    parts = []
    for i, (eid, (image, tests, proven, size)) in enumerate(PARTS.items(), 1):
        it = items[eid]
        parts.append(f"""<section class="part">
  <h3><span class="step">{i}</span> {eid} · {escape(it['label'].capitalize())} <small>at {it['x']:.1f}–{it['x'] + it['w']:.1f} m</small></h3>
  <div class="two">
    {img('concept/' + image, 'Illustration (FLUX 3). Proportions are approximate; the side view below is exact.')}
    <div>
      <p><b>Size:</b> {size}</p>
      <p><b>Tests:</b> {tests}</p>
      <p class="ok"><b>Can the duck do it?</b> {proven}</p>
      {part_profile_svg(it)}
    </div>
  </div>
</section>""")

    OUT.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Microduck Course Plan</title>
<style>
:root {{ --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a65; --line:#e3e0d8; --card:#ffffff; --accent:#c4561d; --code:#f1eee6;
  --floor:#ecebe6; --grid:#d6d3ca; --route:#c4561d; --wood:#d9b07c; --wood-dark:#a8743f; --wet:#7fb6d9; --ok:#2f7d4f; --duck:#f4f1ea; --duck-line:#1d1d1b; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#161614; --fg:#ecebe6; --muted:#a09f99; --line:#2f2e2a; --card:#1e1d1b;
  --accent:#f08a4b; --code:#23221f; --floor:#26251f; --grid:#3a3934; --route:#f08a4b; --wood:#c99a62; --wood-dark:#8e6233; --wet:#4f8fb8; --ok:#6cc792; --duck:#ecebe6; --duck-line:#ecebe6; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:0 16px 80px; }}
.hero {{ position:relative; margin:0 -16px; }}
.hero img {{ width:100%; display:block; max-height:520px; object-fit:cover; }}
.hero .t {{ position:absolute; left:0; right:0; bottom:0; padding:28px 24px 20px; color:#fff; background:linear-gradient(transparent, rgba(0,0,0,.65)); }}
.hero h1 {{ margin:0; font-size:clamp(1.6rem, 4vw, 2.6rem); line-height:1.15; }} .hero p {{ margin:6px 0 0; opacity:.92; }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 0; }}
.chip {{ border:1px solid var(--line); background:var(--card); border-radius:99px; padding:3px 12px; font-size:.85rem; }} .chip b {{ color:var(--accent); }}
h2 {{ margin:2.6em 0 .4em; font-size:1.55rem; }} p.lead {{ margin-top:0; color:var(--muted); max-width:820px; }}
ol.stages {{ list-style:none; padding:0; margin:16px 0; display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:10px; }}
ol.stages li {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; display:flex; flex-direction:column; gap:2px; font-size:.88rem; }}
ol.stages li .n {{ font-weight:700; color:var(--muted); }} ol.stages li b {{ font-size:1rem; }}
ol.stages li span:not(.n) {{ color:var(--muted); }} ol.stages li em {{ font-style:normal; font-size:.78rem; margin-top:auto; color:var(--muted); }}
ol.stages li.now {{ border-color:var(--accent); box-shadow:0 0 0 1px var(--accent) inset; }}
ol.stages li.now .n::after {{ content:" · now"; color:var(--accent); }} ol.stages li.next .n::after {{ content:" · next"; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; align-items:start; }}
@media (max-width:820px) {{ .two {{ grid-template-columns:1fr; }} }}
figure {{ margin:0; }} figure img {{ width:100%; border-radius:8px; border:1px solid var(--line); display:block; }}
figcaption {{ font-size:.84rem; color:var(--muted); margin-top:6px; }}
.part {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:16px 0; }}
.part h3 {{ margin:0 0 12px; font-size:1.2rem; }} .part h3 small {{ color:var(--muted); font-weight:400; font-size:.85rem; }}
.part p {{ margin:.2em 0 .7em; }} .ok {{ color:var(--ok); }} .ok b {{ color:var(--ok); }}
.step {{ display:inline-grid; place-items:center; width:26px; height:26px; border-radius:50%; background:var(--accent); color:#fff; font-size:.85rem; margin-right:4px; }}
svg text {{ font:600 11px -apple-system, sans-serif; }}
.map, .profile {{ width:100%; height:auto; background:var(--card); border:1px solid var(--line); border-radius:8px; }}
.profile {{ margin-top:6px; }}
.map .floor {{ fill:var(--floor); }} .map .grid {{ stroke:var(--grid); }}
.map .route {{ fill:none; stroke:var(--route); stroke-width:3; stroke-dasharray:6 4; }} .arrowhead {{ fill:var(--route); }}
.lbl {{ fill:#1d1d1b; text-anchor:middle; font-size:12px; }} .lbl-sub {{ fill:var(--muted); text-anchor:middle; }}
.scale {{ stroke:var(--fg); stroke-width:2; }} .ground {{ stroke:var(--muted); stroke-width:1.5; }}
.shape {{ stroke:var(--wood-dark); stroke-width:1; }} .shape.walk-on {{ fill:var(--wood); }} .shape.obstacle {{ fill:var(--wood-dark); }}
.shape.slippery {{ fill:var(--wet); stroke:var(--wet); }} .dim {{ fill:var(--muted); font-weight:400; }}
.duck {{ fill:var(--duck); stroke:var(--duck-line); stroke-width:1; }} .duck-foot {{ fill:#e8692c; stroke:var(--duck-line); stroke-width:1; }} .duck-eye {{ fill:#f2b705; stroke:var(--duck-line); }}
.grid8 {{ width:100%; max-width:280px; border-radius:6px; }}
.box-outline {{ fill:none; stroke:var(--accent); stroke-width:3; }} .box-lbl {{ fill:var(--accent); text-anchor:middle; font-size:12px; }}
.facts {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:10px; margin:12px 0; }}
.facts div {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }}
.facts b {{ display:block; font-size:1.25rem; color:var(--accent); }} .facts span {{ font-size:.88rem; color:var(--muted); }}
table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:.9rem; display:block; overflow-x:auto; }}
th, td {{ border:1px solid var(--line); padding:6px 9px; vertical-align:top; text-align:left; }} th {{ background:var(--code); }}
code, pre {{ background:var(--code); border-radius:4px; font-size:.86em; }} code {{ padding:1px 4px; }}
pre {{ padding:12px; overflow-x:auto; font-size:.8em; }} pre code {{ padding:0; }}
blockquote {{ margin:12px 0; padding:4px 16px; border-left:3px solid var(--accent); color:var(--muted); }}
details {{ margin-top:2em; border-top:1px solid var(--line); padding-top:1em; }} summary {{ cursor:pointer; font-size:1.25rem; font-weight:700; }}
.doc h1 {{ display:none; }} .doc h2 {{ font-size:1.25rem; }} .doc h3 {{ color:var(--accent); }}
.gallery {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:12px; margin-top:12px; }}
.gallery figcaption {{ text-transform:capitalize; }}
footer {{ margin-top:3em; font-size:.82rem; color:var(--muted); }}
</style></head>
<body><main>

<header class="hero">
  <img src="{REL}/concept/v2-e3-wet-floor.png" alt="Microduck walking across a wet floor section">
  <div class="t"><h1>Teaching Microduck to see and walk</h1>
  <p>Plan v2: one straight lane, four basic elements, all inside what the duck is already trained to handle.</p></div>
</header>
<div class="chips">
  <span class="chip">Phase <b>1 · Plan</b></span><span class="chip">Next: <b>build E1 in FreeCAD</b></span>
  <span class="chip">Estimated cloud cost: <b>≈ $15–27</b> (≤ $40 with margin)</span><span class="chip">Updated 2026-10-26</span>
</div>

<h2>The robot</h2>
<p class="lead">Official specs (Pollen Robotics, Kingy.ai launch analysis). The full sourced sheet is <code>pipeline/01-plan/robot-specs.md</code>.</p>
<div class="facts">
  <div><b>25 × 14 cm</b><span>tall × wide, under 800 g</span></div>
  <div><b>15 motors</b><span>the walking policy drives 14</span></div>
  <div><b>8 × 8 depth</b><span>time-of-flight sensor + front camera + 2 IMUs</span></div>
  <div><b>50 Hz</b><span>ONNX policy onboard (RK3566)</span></div>
  <div><b>≤ 1.5 cm · ≤ 8° · grip ≥ 0.3</b><span>steps, slopes and floor grip it is already trained for</span></div>
</div>

<h2>The route</h2>
<p class="lead">One straight 6 m lane, about 20–30 s of walking. Start → <b>E1</b> gentle hump → <b>E2</b> low steps → <b>E3</b> wet floor → <b>E4</b> box to walk around → finish. Both drawings are exact (from <code>layout.json</code>).</p>
{course_svg(layout)}
<p class="lead" style="margin-top:14px">Side view at true scale. The elements really are this low compared with the duck.</p>
{route_profile_svg(layout)}

<h2>The route, part by part</h2>
<p class="lead">Each element on its own: an illustration, its exact size, an exact side view with the duck at the same scale, and why it's within the duck's abilities.</p>
{''.join(parts)}

<h2>What the duck "sees"</h2>
<div class="two">
  <div><p>The real duck's depth sensor is an <b>8 × 8 grid</b>: 64 distances, not a camera image. We simulate exactly that (64 rays from the head), so the trained policy gets in simulation what it gets on the robot. It's also much cheaper to simulate than a rendered depth camera.</p>
  <p class="figcaption" style="color:var(--muted);font-size:.84rem">Illustration on the right: light = near, dark = far. The floor gets farther towards the top; the box (outlined) is a block of cells all at the same distance, standing up from the floor. The policy learns to read that pattern. Hover a cell for its distance.</p></div>
  <figure>{depth_grid_svg()}<figcaption>8 × 8 depth grid looking at the box (illustration, not sensor data).</figcaption></figure>
</div>

<h2>Where it trains</h2>
<p class="lead">Isaac Lab 3.0 with Newton physics on one Nebius RTX PRO 6000. 4,096 ducks practise at once, each on a randomised patch of one of the four elements (humps 1–4.4 cm, steps 0.5–1.5 cm, grip 0.2–1.2, boxes in random spots), getting harder as they succeed. It starts from NVIDIA's ready-made Microduck walking policy.</p>
<div class="two">
  {img("concept/06-parallel-training.png", "Thousands of ducks in parallel, each on its own terrain patch (illustration from plan v1).")}
  <div>
    <div class="facts" style="margin-top:0">
      <div><b>≈ 8–15 h</b><span>total VM time: setup, baseline, scene, 3–5 training runs, validation</span></div>
      <div><b>≈ $15–27</b><span>at $1.80/h on-demand; ≤ $40 with a 50 % margin</span></div>
      <div><b>≈ 3–6 GPU-h</b><span>pure training ($5–11); can run preemptible from $0.79/h</span></div>
      <div><b>1–1.5 h</b><span>baseline walking: 3,000 iterations ≈ 295 M steps (Pollen: 1–2 h)</span></div>
    </div>
    <p class="figcaption" style="color:var(--muted);font-size:.84rem">Estimates assume 60–80 k steps/s on one RTX PRO 6000 (NVIDIA reports ≈ 78 k/s per GPU). Phase 4 measures the real speed and these numbers get updated. The boot disk is billed separately while it exists.</p>
  </div>
</div>

<h2>How we check it</h2>
<p class="lead">The trained policy runs on the exact course in Isaac Sim with several ducks. We record completion, falls, slips on E3, collisions with E4, time, and videos.</p>
{img("concept/07-validation-run.png", "Several ducks run the course together (illustration from plan v1; the v2 course is a single straight lane).")}

<h2>The pipeline</h2>
<p class="lead">Same order as the video: design on the Mac first, then train and test in the cloud. Each phase is logged in <code>docs/phase-N-*.md</code>.</p>
<ol class="stages">{stages}</ol>

<details><summary>Full plan</summary><div class="doc">{md("plan.md")}</div></details>
<details><summary>Robot specifications and sources</summary><div class="doc">{md("robot-specs.md")}</div></details>
<details><summary>Video reference frames (NVIDIA)</summary>
<p class="lead">From NVIDIA's GTC Berlin 2026 demo, in the order they appear. Private reference only.</p>
<div class="gallery">{frames}</div></details>

<footer>Renders are AI-generated with BFL FLUX 3 as illustrations; prompts and request ids are in <code>pipeline/01-plan/concept/</code>. Sizes and positions come from <code>plan.md</code> and <code>layout.json</code>; the maps and side views are drawn from that data.</footer>
</main></body></html>
""")
    print(OUT)


if __name__ == "__main__":
    main()
