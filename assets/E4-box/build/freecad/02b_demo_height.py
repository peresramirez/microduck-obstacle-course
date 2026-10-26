# E4 box, optional on-camera demo: change Params.height; walls stay 12 mm and the hand-hole stays 30 mm below the top.
# Vars: DOC, HEIGHT (e.g. "200 mm"). build.sh runs 100, 200, then 150 mm (the spec value).
import FreeCAD as App, FreeCADGui as Gui

doc = App.getDocument(DOC)
doc.Params.set("B4", HEIGHT); doc.recompute()
v = Gui.ActiveDocument.ActiveView; v.viewFront(); Gui.SendMsgToActiveView("ViewFit")
bb = doc.Box.Shape.BoundBox
print("height", HEIGHT, "-> box z", round(bb.ZMax, 3), "mm, valid", doc.Box.Shape.isValid())
