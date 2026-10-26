# E3 wet floor, FreeCAD step 2/3: the tile as a Part::Box bound to Params, from the origin along +x, centred in y,
# inside an App::Part: exporting a bare Part::Box to STEP dropped its placement (y came out 0..600 instead of -300..300).
# Vars: DOC.
import FreeCAD as App, FreeCADGui as Gui
from PySide import QtWidgets

doc = App.getDocument(DOC)
part = doc.addObject("App::Part", "WetFloor"); part.Label = "E3_WetFloor"
t = doc.addObject("Part::Box", "Tile"); t.Label = "E3_WetTile"; part.addObject(t)
t.setExpression("Length", "Params.length"); t.setExpression("Width", "Params.width"); t.setExpression("Height", "Params.thickness")
t.setExpression(".Placement.Base.y", "-Params.width / 2")
doc.recompute()
t.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=(0.78, 0.80, 0.83), Shininess=0.9)]
bb = t.Shape.BoundBox
print("Tile valid", t.Shape.isValid(), "volume_l", round(t.Shape.Volume / 1e6, 3),
      "bbox", [round(v, 3) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)])
mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
for w in mdi.subWindowList():
    if w.windowTitle().startswith(doc.Label):
        mdi.setActiveSubWindow(w)
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
