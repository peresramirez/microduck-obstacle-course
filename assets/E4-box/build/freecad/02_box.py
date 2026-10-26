# E4 box, FreeCAD step 2/3: hollow plywood box with a hand-hole, every size bound to Params.
#   Shell = Outer box - Inner box (walls = Params.wall on all six sides)
#   Box   = Shell - HandHoleCutter (a stadium slot through the -y wall: middle box + two end cylinders)
# Vars: DOC.
import FreeCAD as App, FreeCADGui as Gui
from PySide import QtWidgets

doc = App.getDocument(DOC)


def box(name, L, W, H, x, y, z):
    b = doc.addObject("Part::Box", name)
    for prop, expr in (("Length", L), ("Width", W), ("Height", H),
                       (".Placement.Base.x", x), (".Placement.Base.y", y), (".Placement.Base.z", z)):
        b.setExpression(prop, expr)
    return b


outer = box("Outer", "Params.length", "Params.width", "Params.height", "0 mm", "-Params.width / 2", "0 mm")
inner = box("Inner", "Params.length - 2 * Params.wall", "Params.width - 2 * Params.wall", "Params.height - 2 * Params.wall",
            "Params.wall", "-Params.width / 2 + Params.wall", "Params.wall")
shell = doc.addObject("Part::Cut", "Shell"); shell.Base = outer; shell.Tool = inner
# hand-hole: the cutter pokes 1 mm out on both sides of the -y wall so the cut is clean
mid = box("HoleMid", "Params.hole_length - Params.hole_height", "Params.wall + 2 mm", "Params.hole_height",
          "Params.length / 2 - (Params.hole_length - Params.hole_height) / 2", "-Params.width / 2 - 1 mm",
          "Params.height - Params.hole_top_offset - Params.hole_height")
ends = []
for name, sign in (("HoleEndA", "-"), ("HoleEndB", "+")):
    c = doc.addObject("Part::Cylinder", name)
    c.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), -90)        # cylinder axis along +y
    c.setExpression("Radius", "Params.hole_height / 2"); c.setExpression("Height", "Params.wall + 2 mm")
    c.setExpression(".Placement.Base.x", f"Params.length / 2 {sign} (Params.hole_length - Params.hole_height) / 2")
    c.setExpression(".Placement.Base.y", "-Params.width / 2 - 1 mm")
    c.setExpression(".Placement.Base.z", "Params.height - Params.hole_top_offset - Params.hole_height / 2")
    ends.append(c)
cutter = doc.addObject("Part::MultiFuse", "HandHoleCutter"); cutter.Shapes = [mid] + ends
result = doc.addObject("Part::Cut", "Box"); result.Label = "E4_Box"; result.Base = shell; result.Tool = cutter
doc.recompute()
for o in (outer, inner, shell, mid, *ends, cutter):
    o.ViewObject.Visibility = False
result.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=(0.86, 0.74, 0.55))]
s = result.Shape; bb = s.BoundBox
print("Box valid", s.isValid(), "solids", len(s.Solids), "volume_l", round(s.Volume / 1e6, 4),
      "bbox", [round(v, 3) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)], "faces", len(s.Faces))
mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
for w in mdi.subWindowList():
    if w.windowTitle().startswith(doc.Label):
        mdi.setActiveSubWindow(w)
Gui.ActiveDocument.ActiveView.viewIsometric()
Gui.SendMsgToActiveView("ViewFit")
