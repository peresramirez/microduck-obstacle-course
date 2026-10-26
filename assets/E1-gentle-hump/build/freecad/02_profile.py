# E1 gentle hump, FreeCAD step 2/4: PartDesign body + cosine profile sketch on the XZ plane.
# 32-segment polyline with every vertex tied to Params by expressions, closed by the base line.
# Vars: DOC.
import math
import FreeCAD as App, FreeCADGui as Gui, Part, Sketcher
from PySide import QtWidgets

doc = App.getDocument(DOC)
Gui.activateWorkbench("PartDesignWorkbench")
body = doc.addObject("PartDesign::Body", "Body"); body.Label = "E1_GentleHump"
xz = [f for f in body.Origin.OriginFeatures if f.Role == "XZ_Plane"][0]
sk = body.newObject("Sketcher::SketchObject", "Profile")
sk.AttachmentSupport = (xz, [""]); sk.MapMode = "FlatFace"
doc.recompute()

N, L, C = 32, 1000.0, 33.0
pts = [App.Vector(L * k / N, C / 2 * (1 - math.cos(2 * math.pi * k / N)), 0) for k in range(N + 1)]
for k in range(N):
    sk.addGeometry(Part.LineSegment(pts[k], pts[k + 1]))
base = sk.addGeometry(Part.LineSegment(pts[N], pts[0]))
cons = [Sketcher.Constraint("Coincident", k, 2, k + 1, 1) for k in range(N - 1)]
cons += [Sketcher.Constraint("Coincident", N - 1, 2, base, 1),
         Sketcher.Constraint("Coincident", base, 2, 0, 1),
         Sketcher.Constraint("Coincident", 0, 1, -1, 1),        # first vertex on the origin
         Sketcher.Constraint("PointOnObject", base, 1, -1)]     # last vertex on the horizontal axis
sk.addConstraint(cons)
# vertex k: x = length*k/N, z = crest/2*(1-cos(360*k/N)); FreeCAD's cos() takes degrees
for k in range(1, N + 1):
    cx = sk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, k - 1, 2, pts[k].x))
    sk.setExpression(f"Constraints[{cx}]", f"Params.length * {k} / {N}")
    if k < N:
        cy = sk.addConstraint(Sketcher.Constraint("DistanceY", -1, 1, k - 1, 2, pts[k].y))
        sk.setExpression(f"Constraints[{cy}]", f"Params.crest / 2 * (1 - cos(360 * {k} / {N}))")
doc.recompute()
b = sk.Shape.BoundBox
print("solve", sk.solve(), "fully constrained:", sk.FullyConstrained, "constraints", len(sk.Constraints),
      "expr", len(sk.ExpressionEngine), "bbox x", round(b.XMin, 3), round(b.XMax, 3), "z", round(b.ZMin, 3), round(b.ZMax, 3))

# the spreadsheet tab is the active view after step 1; switch to the 3D view of this document
mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
for w in mdi.subWindowList():
    if w.windowTitle().startswith(doc.Label):
        mdi.setActiveSubWindow(w)
Gui.ActiveDocument.ActiveView.viewFront(); Gui.SendMsgToActiveView("ViewFit")
