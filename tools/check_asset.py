"""Measure an exported asset (model.usd + model.glb) and check it against the expected size.

Checks: USD stage is Z-up, 1 m per unit, has a default prim; USD and GLB bounding boxes match the
expected size (±1 mm); every texture the USD references exists; the steepest walkable face
(normal within 60° of up) stays under --max-slope; with --part, a named mesh sits exactly where
expected. Prints a Markdown table for NOTES.md.

Run from isaac-obstacle-course/:
  uv run --no-project --with usd-core --with trimesh --with numpy python tools/check_asset.py \
      assets/E1-gentle-hump --size 1.0 0.6 0.033 --max-slope 6.0
  … assets/E2-low-steps --size 1.2 0.6 0.02 --part E2_TopSheet 0.2 1.0 -0.3 0.3 0.01 0.02
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from pxr import Sdf, Usd, UsdGeom, UsdShade

TOL = 0.001  # metres


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("asset", type=Path)
    ap.add_argument("--size", type=float, nargs=3, required=True, metavar=("X", "Y", "Z"))
    ap.add_argument("--max-slope", type=float, help="degrees, walkable faces only")
    ap.add_argument("--part", nargs=7, action="append", default=[], metavar=("NAME", "XMIN", "XMAX", "YMIN", "YMAX", "ZMIN", "ZMAX"),
                    help="a mesh prim whose name contains NAME must have this world bounding box (m)")
    a = ap.parse_args()
    rows = []

    def check(name, ok, value):
        rows.append((name, "✅" if ok else "❌", value))

    stage = Usd.Stage.Open(str(a.asset / "model.usd"))
    check("USD up axis", UsdGeom.GetStageUpAxis(stage) == "Z", UsdGeom.GetStageUpAxis(stage))
    check("USD metres per unit", UsdGeom.GetStageMetersPerUnit(stage) == 1.0, UsdGeom.GetStageMetersPerUnit(stage))
    dp = stage.GetDefaultPrim()
    check("USD default prim", bool(dp), dp.GetPath() if dp else "none")

    box = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]).ComputeWorldBound(stage.GetPseudoRoot()).ComputeAlignedRange()
    lo, hi = np.array(box.GetMin()), np.array(box.GetMax())
    size = hi - lo
    check("USD size (m)", np.allclose(size, a.size, atol=TOL), " × ".join(f"{v:.4f}" for v in size))
    check("USD origin (bottom-centre of start edge)", np.allclose([lo[0], (lo[1] + hi[1]) / 2, lo[2]], 0, atol=TOL),
          f"x0 {lo[0]:.4f}, y-centre {(lo[1] + hi[1]) / 2:.4f}, z0 {lo[2]:.4f}")

    meshes = [UsdGeom.Mesh(p) for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]
    check("USD meshes", len(meshes) > 0, len(meshes))
    missing, bound = [], 0
    for p in stage.Traverse():
        if UsdShade.MaterialBindingAPI(p).ComputeBoundMaterial()[0] and p.IsA(UsdGeom.Mesh):
            bound += 1
        for attr in p.GetAttributes():
            if attr.GetTypeName() == Sdf.ValueTypeNames.Asset and attr.Get():
                path = attr.Get().resolvedPath or attr.Get().path
                if not Path(path).is_absolute():
                    path = a.asset / path
                if not Path(path).exists():
                    missing.append(str(attr.Get().path))
    check("USD meshes with a material", bound == len(meshes), f"{bound}/{len(meshes)}")
    check("USD textures found", not missing, "all" if not missing else ", ".join(missing))

    steepest = 0.0
    for m in meshes:
        pts = np.array(m.GetPointsAttr().Get())
        counts, idx = m.GetFaceVertexCountsAttr().Get(), np.array(m.GetFaceVertexIndicesAttr().Get())
        xf = np.array(m.ComputeLocalToWorldTransform(Usd.TimeCode.Default())).T
        pts = (np.c_[pts, np.ones(len(pts))] @ xf.T)[:, :3]
        i = 0
        for c in counts:
            v = pts[idx[i:i + c]]; i += c
            n = np.cross(v[1] - v[0], v[2] - v[0])
            if np.linalg.norm(n) < 1e-12:
                continue
            n /= np.linalg.norm(n)
            if n[2] > math.cos(math.radians(60)):
                steepest = max(steepest, math.degrees(math.acos(min(1.0, n[2]))))
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"])
    for name, *want in a.part:
        hits = [m for m in meshes if name in m.GetPath().pathString]
        if len(hits) != 1:
            check(f"part {name}", False, f"{len(hits)} meshes match")
            continue
        r = cache.ComputeWorldBound(hits[0].GetPrim()).ComputeAlignedRange()
        got = [r.GetMin()[0], r.GetMax()[0], r.GetMin()[1], r.GetMax()[1], r.GetMin()[2], r.GetMax()[2]]
        check(f"part {name} (x, y, z ranges, m)", np.allclose(got, [float(v) for v in want], atol=TOL),
              ", ".join(f"{got[i]:.4f}–{got[i + 1]:.4f}" for i in (0, 2, 4)))
    if a.max_slope is not None:
        check("steepest walkable face", steepest <= a.max_slope, f"{steepest:.2f}° (limit {a.max_slope}°)")

    glb = trimesh.load(a.asset / "model.glb", force="scene")
    glo, ghi = glb.bounds                      # glTF is Y-up: (x, y, z)_gltf = (x, z, -y)_usd
    gsize = np.array([ghi[0] - glo[0], ghi[2] - glo[2], ghi[1] - glo[1]])
    check("GLB size (m)", np.allclose(gsize, a.size, atol=TOL), " × ".join(f"{v:.4f}" for v in gsize))
    tris = sum(len(g.faces) for g in glb.geometry.values())
    check("GLB triangles", tris > 0, tris)

    print("| Check | | Value |\n|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} |")
    sys.exit(0 if all(r[1] == "✅" for r in rows) else 1)


if __name__ == "__main__":
    main()
