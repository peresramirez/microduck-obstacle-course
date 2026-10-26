"""Build ``scenes/course.usd``: the real course as one USD scene with physics, then check it against the manifest.

The same collision geometry as the training task (``training/isaaclab_ext/course_geometry.py``, scale 1 = real
heights), written as UsdPhysics colliders with friction materials, plus our textured phase 2 assets as visuals:

  /World                              default prim, Z-up, metres
    PhysicsScene                      gravity -Z 9.81
    Course/Collision/<part>           invisible colliders: floor plane, E1 hump (triangle mesh), E2 sheets, E3 tile, E4 box
    Course/Visuals/<asset>            references to ../assets/<id>/model.usd (no physics)
    Course/Route                      the route the ducks are steered along (guide curve) + Start / Finish markers
    Materials/Physics/<name>          UsdPhysics materials (friction from the manifest)

The wet tile carries ``mjc:priority = 1`` so that, in Newton's MuJoCo solver, its friction 0.3 wins over the foot's
(the solver otherwise takes the larger of the two). Run from isaac-obstacle-course/ on the Mac:

    uv run --no-project --with usd-core --with trimesh --with numpy python scenes/build_course_usd.py
"""

import json
import sys
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training" / "isaaclab_ext"))
import course_geometry as geo  # noqa: E402

OUT = ROOT / "scenes" / "course.usd"
MANIFEST = json.loads((ROOT / "pipeline" / "02-course-preview" / "course_manifest.json").read_text())

MATERIALS = {"Concrete_mu1_0": 1.0, "Plywood_mu1_0": 1.0, "WetTile_mu0_3": geo.E3["friction"], "BoxPlywood_mu0_8": 0.8}
PARTS = {  # collider name -> (mesh, physics material, manifest prim it must match)
    "F_LaneFloor": (None, "Concrete_mu1_0", "/F_floor/F_LaneFloor"),
    "E1_GentleHump": ("E1_hump", "Plywood_mu1_0", "/E1_gentle_hump/E1_GentleHump"),
    "E2_BottomSheet": ("E2_bottom", "Plywood_mu1_0", "/E2_low_steps/E2_BottomSheet"),
    "E2_TopSheet": ("E2_top", "Plywood_mu1_0", "/E2_low_steps/E2_TopSheet"),
    "E3_WetTile": ("wet", "WetTile_mu0_3", "/E3_wet_floor/E3_WetTile"),
    "E4_Box": ("E4_box", "BoxPlywood_mu0_8", "/E4_box/E4_Box"),
}
VISUALS = {"F_floor": "F-floor", "E1_gentle_hump": "E1-gentle-hump", "E2_low_steps": "E2-low-steps",
           "E3_wet_floor": "E3-wet-floor", "E4_box": "E4-box"}


def floor_mesh():
    import trimesh

    w = geo.LANE_WIDTH / 2
    return trimesh.Trimesh(vertices=[[0, -w, 0], [geo.LANE_LENGTH, -w, 0], [geo.LANE_LENGTH, w, 0], [0, w, 0]],
                           faces=[[0, 1, 2], [0, 2, 3]])


def build() -> None:
    meshes = {**geo.solid_meshes(1.0), "wet": geo.wet_tile_mesh()}
    stage = Usd.Stage.CreateNew(str(OUT))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    world.GetPrim().SetCustomDataByKey("source", "scenes/build_course_usd.py (course_geometry.py, course_manifest.json)")
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(9.81)

    for name, mu in MATERIALS.items():
        mat = UsdShade.Material.Define(stage, f"/World/Materials/Physics/{name}")
        api = UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
        api.CreateStaticFrictionAttr(mu)
        api.CreateDynamicFrictionAttr(mu)
        api.CreateRestitutionAttr(0.0)

    UsdGeom.Scope.Define(stage, "/World/Course/Collision")
    for name, (key, mat_name, _) in PARTS.items():
        tm = floor_mesh() if key is None else meshes[key]
        mesh = UsdGeom.Mesh.Define(stage, f"/World/Course/Collision/{name}")
        mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float, v)) for v in tm.vertices]))
        mesh.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(tm.faces)))
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([int(i) for i in tm.faces.flatten()]))
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        mesh.CreatePurposeAttr(UsdGeom.Tokens.guide)  # colliders are not rendered; the visuals are
        prim = mesh.GetPrim()
        UsdPhysics.CollisionAPI.Apply(prim)
        approx = "none" if name in ("E1_GentleHump", "F_LaneFloor") else "convexHull"  # triangle mesh / box
        UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(approx)
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(
            UsdShade.Material(stage.GetPrimAtPath(f"/World/Materials/Physics/{mat_name}")),
            UsdShade.Tokens.weakerThanDescendants, "physics")
        if name == "E3_WetTile":
            prim.CreateAttribute("mjc:priority", Sdf.ValueTypeNames.Int).Set(1)

    for asset in MANIFEST["assets"]:
        prim_name = asset["default_prim"].strip("/")
        xf = UsdGeom.Xform.Define(stage, f"/World/Course/Visuals/{prim_name}")
        xf.AddTranslateOp().Set(Gf.Vec3d(*asset["origin_lane"]))
        xf.GetPrim().GetReferences().AddReference(f"../assets/{VISUALS[prim_name]}/model.usd")

    route = UsdGeom.BasisCurves.Define(stage, "/World/Course/Route/Path")
    route.CreateTypeAttr(UsdGeom.Tokens.linear)
    route.CreatePointsAttr([Gf.Vec3f(x, y, 0.005) for x, y in geo.ROUTE])
    route.CreateCurveVertexCountsAttr([len(geo.ROUTE)])
    route.CreatePurposeAttr(UsdGeom.Tokens.guide)
    for label, x in (("Start", geo.START_X), ("Finish", geo.FINISH_X)):
        UsdGeom.Xform.Define(stage, f"/World/Course/Route/{label}").AddTranslateOp().Set(Gf.Vec3d(x, 0, 0))
    stage.GetRootLayer().Save()


def check() -> bool:
    """Every collider's world bounds must match the manifest (origin_lane + bounds_local) within 1 mm."""
    stage = Usd.Stage.Open(str(OUT))
    want = {}
    for asset in MANIFEST["assets"]:
        for part in asset["parts"]:
            lo, hi = part["bounds_local"]
            o = asset["origin_lane"]
            want[part["prim"]] = ([lo[i] + o[i] for i in range(3)], [hi[i] + o[i] for i in range(3)], part)
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.guide])
    ok_all = True
    for name, (_, mat_name, manifest_prim) in PARTS.items():
        prim = stage.GetPrimAtPath(f"/World/Course/Collision/{name}")
        box = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        lo, hi = list(box.GetMin()), list(box.GetMax())
        wlo, whi, part = want[manifest_prim]
        err = max(max(abs(a - b) for a, b in zip(lo, wlo)), max(abs(a - b) for a, b in zip(hi, whi)))
        mu = MATERIALS[mat_name]
        ok = err < 1e-3 and prim.HasAPI(UsdPhysics.CollisionAPI) and abs(mu - part["static_friction"]) < 1e-6
        ok_all &= ok
        extra = ", mjc:priority 1" if prim.GetAttribute("mjc:priority").Get() == 1 else ""
        print(f"{'✅' if ok else '❌'} {name:15s} bounds {[round(v, 4) for v in lo]} – {[round(v, 4) for v in hi]}"
              f" (max error {err * 1000:.2f} mm), friction {mu}{extra}")
    refs = [p for p in stage.Traverse() if p.GetPath().pathString.startswith("/World/Course/Visuals/") and
            p.GetParent().GetPath().pathString == "/World/Course/Visuals"]
    resolved = all(len(list(p.GetChildren())) > 0 for p in refs)
    print(f"{'✅' if resolved else '❌'} {len(refs)} visual assets referenced and resolved")
    print(f"{'✅' if UsdGeom.GetStageUpAxis(stage) == 'Z' and UsdGeom.GetStageMetersPerUnit(stage) == 1.0 else '❌'}"
          " Z-up, metres")
    return ok_all and resolved


if __name__ == "__main__":
    build()
    print(f"wrote {OUT.relative_to(ROOT)}")
    sys.exit(0 if check() else 1)
