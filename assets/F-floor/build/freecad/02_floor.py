# F floor and lane, FreeCAD step 2/3: the lane surface as a Part::Plane at z = 0 (props sit on it), from the
# origin along +x, centred in y, inside an App::Part (keeps its placement in STEP, see E3). The tape lines are
# drawn as thin view-only Part::Plane rectangles (0.5 mm above the floor; not exported).
# Vars: DOC.
import FreeCAD as App, FreeCADGui as Gui
from PySide import QtWidgets

doc = App.getDocument(DOC)
part = doc.addObject("App::Part", "FloorPart"); part.Label = "F_Floor"
f = doc.addObject("Part::Plane", "Floor"); f.Label = "F_LaneFloor"; part.addObject(f)
f.setExpression("Length", "Params.length"); f.setExpression("Width", "Params.width")
f.setExpression(".Placement.Base.y", "-Params.width / 2")
refs = []
for name, cx in (("StartTape", "Params.start_line_x"), ("FinishTape", "Params.finish_line_x")):
    t = doc.addObject("Part::Plane", name); t.Label = name + "_viewonly"
    t.setExpression("Length", "Params.tape_width"); t.setExpression("Width", "Params.width")
    t.setExpression(".Placement.Base.x", f"{cx} - Params.tape_width / 2")
    t.setExpression(".Placement.Base.y", "-Params.width / 2"); t.setExpression(".Placement.Base.z", "0.5 mm")
    refs.append(t)
doc.recompute()
f.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=(0.70, 0.70, 0.69))]
for t in refs:
    t.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=(0.97, 0.97, 0.97))]
bb = f.Shape.BoundBox
print("Floor valid", f.Shape.isValid(), "area_m2", round(f.Shape.Area / 1e6, 4),
      "bbox", [round(v, 3) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)],
      "tapes x", [round(t.Shape.BoundBox.XMin, 1) for t in refs])
mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
for w in mdi.subWindowList():
    if w.windowTitle().startswith(doc.Label):
        mdi.setActiveSubWindow(w)
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
