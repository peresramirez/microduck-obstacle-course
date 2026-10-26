"""Check the whole course: every exported asset placed at its layout.json position, measured from its model.usd.

Checks: each element lies on the floor; walk-on and obstacle footprints don't overlap; heights stay inside the
duck's envelope (step per sheet <= 1.5 cm, hump crest <= 4.4 cm, wet tile <= 5 mm, box lower than the 25 cm duck);
the route starts on the start tape and ends on the finish tape, stays inside the lane with the duck's half width,
never crosses the box, and keeps a clearance around it. Prints a Markdown table.

Run from isaac-obstacle-course/:
  uv run --no-project --with usd-core --with numpy python tools/check_course.py [--clearance 0.05]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from pxr import Usd, UsdGeom

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = {"F": "F-floor", "E1": "E1-gentle-hump", "E2": "E2-low-steps", "E3": "E3-wet-floor", "E4": "E4-box"}
DUCK_HALF_WIDTH = 0.07        # 14 cm wide (robot-specs.md)
DUCK_HEIGHT = 0.25


def boxes(asset):
    """World-aligned bounds of the whole asset and of each mesh, in the asset's own frame."""
    st = Usd.Stage.Open(str(ROOT / "assets" / FOLDERS[asset] / "model.usd"))
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"])
    rng = lambda p: cache.ComputeWorldBound(p).ComputeAlignedRange()
    whole = rng(st.GetPseudoRoot())
    parts = {p.GetName(): rng(p) for p in st.Traverse() if p.IsA(UsdGeom.Mesh)}
    as_np = lambda r: (np.array(r.GetMin()), np.array(r.GetMax()))
    return as_np(whole), {k: as_np(v) for k, v in parts.items()}


def seg_rect_distance(a, b, lo, hi, n=2000):
    """Smallest distance from segment a-b to an axis-aligned rectangle (2D), sampled."""
    t = np.linspace(0, 1, n)[:, None]
    p = a + t * (b - a)
    d = np.maximum(np.maximum(lo - p, p - hi), 0)
    return float(np.min(np.hypot(d[:, 0], d[:, 1])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clearance", type=float, default=0.05, help="min gap between the duck's side and the box (m)")
    a = ap.parse_args()
    lay = json.load(open(ROOT / "pipeline/01-plan/layout.json"))
    half = lay["floor"]["d"] / 2
    items = {it["id"]: it for it in lay["items"]}
    place = {"F": np.array([0.0, 0.0, 0.0])}
    for k in ("E1", "E2", "E3", "E4"):
        it = items[k]
        place[k] = np.array([it["x"], it["y"] + it["d"] / 2 - half, 0.0])
    world, parts = {}, {}
    for k in FOLDERS:
        (lo, hi), pp = boxes(k)
        world[k] = (lo + place[k], hi + place[k])
        parts[k] = {n: (l + place[k], h + place[k]) for n, (l, h) in pp.items()}
    rows = []
    check = lambda name, ok, val: rows.append((name, "✅" if ok else "❌", val))
    fmt = lambda lo, hi: f"x {lo[0]:.3f}–{hi[0]:.3f}, y {lo[1]:.3f}–{hi[1]:.3f}, z {lo[2]:.3f}–{hi[2]:.3f}"

    flo, fhi = world["F"]
    check("floor at z = 0, 6.0 × 1.2 m", np.allclose([flo[2], fhi[2], fhi[0] - flo[0], fhi[1] - flo[1]], [0, 0, 6.0, 1.2], atol=1e-3), fmt(flo, fhi))
    for k in ("E1", "E2", "E3", "E4"):
        lo, hi = world[k]
        on = lo[0] >= flo[0] - 1e-6 and hi[0] <= fhi[0] + 1e-6 and lo[1] >= flo[1] - 1e-6 and hi[1] <= fhi[1] + 1e-6 and abs(lo[2]) < 1e-4
        check(f"{k} on the floor", on, fmt(lo, hi))
    ks = ["E1", "E2", "E3", "E4"]
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            (l1, h1), (l2, h2) = world[ks[i]], world[ks[j]]
            overlap = (min(h1[0], h2[0]) - max(l1[0], l2[0]) > 1e-6) and (min(h1[1], h2[1]) - max(l1[1], l2[1]) > 1e-6)
            if overlap:
                check(f"{ks[i]} / {ks[j]} footprints", False, "overlap")
    check("no footprint overlaps (E1–E4)", not any(r[0].endswith("footprints") for r in rows), "pairwise x-y check")
    gaps = [(ks[i], ks[i + 1], world[ks[i + 1]][0][0] - world[ks[i]][1][0]) for i in range(3)]
    check("flat floor between elements", all(g > 0.2 for *_, g in gaps), ", ".join(f"{p}→{q} {g:.2f} m" for p, q, g in gaps))
    # heights
    check("E1 crest ≤ 4.4 cm (training max)", world["E1"][1][2] <= 0.044 + 1e-6, f"{world['E1'][1][2] * 100:.1f} cm")
    tops = sorted(h[2] for _, h in parts["E2"].values())
    rises = [tops[0]] + [tops[i] - tops[i - 1] for i in range(1, len(tops))]
    check("E2 each step ≤ 1.5 cm", max(rises) <= 0.015 + 1e-6, " + ".join(f"{r * 100:.1f} cm" for r in rises))
    check("E3 tile ≤ 5 mm (not a step)", world["E3"][1][2] <= 0.005, f"{world['E3'][1][2] * 1000:.1f} mm")
    check("E4 lower than the duck (walk around)", world["E4"][1][2] < DUCK_HEIGHT, f"{world['E4'][1][2] * 100:.0f} cm < {DUCK_HEIGHT * 100:.0f} cm")
    # route
    route = np.array([(x, y - half) for x, y in lay["route"]])
    tape = lambda cx: (cx - 0.025, cx + 0.025)
    s0, s1 = tape(0.40); f0, f1 = tape(5.60)
    check("route starts on the start tape", s0 <= route[0][0] <= s1, f"x {route[0][0]:.2f} (tape {s0:.3f}–{s1:.3f})")
    check("route ends on the finish tape", f0 <= route[-1][0] <= f1, f"x {route[-1][0]:.2f} (tape {f0:.3f}–{f1:.3f})")
    edge = float(np.max(np.abs(route[:, 1])) + DUCK_HALF_WIDTH)
    check("duck stays inside the lane", edge <= half, f"max |y| + half width = {edge:.2f} m ≤ {half:.2f}")
    l4, h4 = world["E4"][0][:2], world["E4"][1][:2]
    dmin = min(seg_rect_distance(route[i], route[i + 1], l4, h4) for i in range(len(route) - 1))
    check("route never crosses E4", dmin > 0, f"closest approach {dmin:.3f} m")
    check(f"clearance duck side ↔ E4 ≥ {a.clearance * 100:.0f} cm", dmin - DUCK_HALF_WIDTH >= a.clearance,
          f"{dmin:.3f} − {DUCK_HALF_WIDTH:.2f} = {dmin - DUCK_HALF_WIDTH:.3f} m")
    on = [k for k in ("E1", "E2", "E3") if world[k][0][1] + DUCK_HALF_WIDTH <= 0 <= world[k][1][1] - DUCK_HALF_WIDTH]
    check("route runs over E1, E2, E3 (duck fully on them)", on == ["E1", "E2", "E3"], ", ".join(on))
    print("| Check | | Value |\n|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} |")
    sys.exit(0 if all(r[1] == "✅" for r in rows) else 1)


if __name__ == "__main__":
    main()
