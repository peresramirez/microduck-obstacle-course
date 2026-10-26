# E2 low steps, FreeCAD step 2/3: two plywood sheets as separate boxes in one App::Part, every size and
# position bound to Params. Bottom: bottom_length x width x rise from the origin; top: top_length x width x
# rise, starting one tread in, sitting on the bottom sheet. Vars: DOC.
import FreeCAD as App, FreeCADGui as Gui
from PySide import QtWidgets

doc = App.getDocument(DOC)
part = doc.addObject("App::Part", "LowSteps"); part.Label = "E2_LowSteps"
sheets = {}
for name, length, x, z in (("BottomSheet", "Params.bottom_length", "0 mm", "0 mm"),
                           ("TopSheet", "Params.top_length", "Params.tread", "Params.rise")):
    b = doc.addObject("Part::Box", name); b.Label = "E2_" + name
    b.setExpression("Length", length); b.setExpression("Width", "Params.width"); b.setExpression("Height", "Params.rise")
    b.setExpression(".Placement.Base.x", x); b.setExpression(".Placement.Base.y", "-Params.width / 2")
    b.setExpression(".Placement.Base.z", z)
    part.addObject(b); sheets[name] = b
doc.recompute()
for b, rgb in ((sheets["BottomSheet"], (0.86, 0.74, 0.55)), (sheets["TopSheet"], (0.80, 0.66, 0.46))):
    b.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=rgb)]
for name, b in sheets.items():
    bb = b.Shape.BoundBox
    print(name, "valid", b.Shape.isValid(), "volume_l", round(b.Shape.Volume / 1e6, 3),
          "bbox", [round(v, 3) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)])
# the spreadsheet tab is the active view after step 1; switch to the 3D view of this document
mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
for w in mdi.subWindowList():
    if w.windowTitle().startswith(doc.Label):
        mdi.setActiveSubWindow(w)
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
