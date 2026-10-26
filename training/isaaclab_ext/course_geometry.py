"""Collision geometry and route of our obstacle course, shared by the Isaac Lab task and the scene exporter.

Pure numpy + trimesh (no Isaac Lab), so ``export_course_usd.py`` can run it on the Mac.

Lane frame: x along the lane from its start edge (0) to 6 m, y across it with y = 0 on the lane centre, z up,
metres. Numbers come from ``pipeline/01-plan/layout.json`` and ``pipeline/02-course-preview/course_manifest.json``
(layout y minus 0.6). In a terrain tile the lane frame starts at ``LANE_X0`` from the tile's low-x edge, centred in y.

``scale`` multiplies the two height parameters that training varies: E1's crest and E2's sheet rise. 1.0 is the real
course (crest 3.3 cm, two 1 cm sheets); the training tiles use ``scale = 0.5 + difficulty`` (0.5 to 1.5).
"""

import math

import numpy as np
import trimesh

LANE_LENGTH, LANE_WIDTH = 6.0, 1.2
LANE_X0 = 1.0
"""Tile-local x of the lane start [m]; leaves 1 m of flat floor before the start and after the lane end."""

E1 = {"x0": 0.8, "length": 1.0, "width": 0.6, "crest": 0.033}
"""Gentle hump: cosine profile z(u) = crest / 2 * (1 - cos(2 pi u / length)), u in [0, length]."""
E2 = {"x0": 2.2, "bottom_length": 1.2, "top_x0": 0.2, "top_length": 0.8, "width": 0.6, "rise": 0.010}
"""Low steps: two stacked sheets; the top one starts ``top_x0`` after the bottom one."""
E3 = {"x0": 3.8, "length": 0.8, "width": 0.6, "thickness": 0.002, "friction": 0.3}
"""Wet floor: a 2 mm tile, friction 0.3 (imported separately so it can carry its own friction)."""
E4 = {"x0": 5.1, "size": 0.2, "height": 0.15}
"""Box: 20 x 20 x 15 cm, centred on the lane; the route goes around it."""

ROUTE = ((0.40, 0.0), (4.85, 0.0), (5.0, 0.3), (5.4, 0.3), (5.5, 0.0), (5.58, 0.0))
"""Route the ducks are steered along (layout.json ``route``, lane frame) [m]."""
START_X, FINISH_X = ROUTE[0][0], ROUTE[-1][0]

ELEMENTS = {  # lane-frame x extent of each element, for the evaluation report
    "E1 hump": (E1["x0"], E1["x0"] + E1["length"]),
    "E2 steps": (E2["x0"], E2["x0"] + E2["bottom_length"]),
    "E3 wet floor": (E3["x0"], E3["x0"] + E3["length"]),
    "E4 box detour": (4.85, 5.5),
}

FLAT_STARTS = ((0.30, 0.70), (1.85, 2.15), (3.45, 4.60), (4.62, 4.80))
"""Lane-frame x ranges where a duck can be spawned on flat floor (or the 2 mm wet tile) during training [m]."""


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> trimesh.Trimesh:
    extents = (x1 - x0, y1 - y0, z1 - z0)
    centre = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return trimesh.creation.box(extents=extents, transform=trimesh.transformations.translation_matrix(centre))


def hump_mesh(crest: float, segments: int = 60) -> trimesh.Trimesh:
    """Closed mesh of the E1 cosine hump in the lane frame."""
    length, half = E1["length"], E1["width"] / 2
    u = np.linspace(0.0, length, segments + 1)
    z = crest / 2 * (1 - np.cos(2 * math.pi * u / length))
    x = E1["x0"] + u
    n = len(x)
    # vertex rings: top-left, top-right, bottom-left, bottom-right for each x
    verts = np.concatenate(
        [np.stack([x, np.full(n, -half), z], 1), np.stack([x, np.full(n, half), z], 1),
         np.stack([x, np.full(n, -half), np.zeros(n)], 1), np.stack([x, np.full(n, half), np.zeros(n)], 1)]
    )
    tl, tr, bl, br = (np.arange(n) + k * n for k in range(4))
    faces = []
    for i in range(n - 1):
        faces += [[tl[i], tr[i + 1], tr[i]], [tl[i], tl[i + 1], tr[i + 1]]]  # top (normal up)
        faces += [[bl[i], br[i], br[i + 1]], [bl[i], br[i + 1], bl[i + 1]]]  # bottom (normal down)
        faces += [[bl[i], tl[i + 1], tl[i]], [bl[i], bl[i + 1], tl[i + 1]]]  # side y = -half
        faces += [[br[i], tr[i], tr[i + 1]], [br[i], tr[i + 1], br[i + 1]]]  # side y = +half
    # process=True merges the coincident top/bottom vertices at both ends (z = 0 there), closing the mesh; the side
    # triangles that collapse there are then dropped
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def solid_meshes(scale: float = 1.0) -> dict[str, trimesh.Trimesh]:
    """Lane-frame collision meshes of E1, E2 (two sheets) and E4. E3 is separate (``wet_tile_mesh``)."""
    rise = E2["rise"] * scale
    w2 = E2["width"] / 2
    s = E4["size"] / 2
    return {
        "E1_hump": hump_mesh(E1["crest"] * scale),
        "E2_bottom": _box(E2["x0"], E2["x0"] + E2["bottom_length"], -w2, w2, 0.0, rise),
        "E2_top": _box(E2["x0"] + E2["top_x0"], E2["x0"] + E2["top_x0"] + E2["top_length"], -w2, w2, rise, 2 * rise),
        "E4_box": _box(E4["x0"], E4["x0"] + E4["size"], -s, s, 0.0, E4["height"]),
    }


def wet_tile_mesh() -> trimesh.Trimesh:
    w = E3["width"] / 2
    return _box(E3["x0"], E3["x0"] + E3["length"], -w, w, 0.0, E3["thickness"])


def box_bounds() -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Lane-frame AABB of the E4 box: (min xyz, max xyz) [m]."""
    s = E4["size"] / 2
    return (E4["x0"], -s, 0.0), (E4["x0"] + E4["size"], s, E4["height"])


def route_y(x: np.ndarray) -> np.ndarray:
    """Route y at lane-frame x (the route is a function of x) [m]."""
    xs, ys = zip(*ROUTE)
    return np.interp(x, xs, ys)
