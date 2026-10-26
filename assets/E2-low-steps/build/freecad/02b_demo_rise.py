# E2 low steps, optional on-camera demo: change Params.rise; both sheets get thicker and the top one moves up.
# Vars: DOC, RISE (e.g. "15 mm"). build.sh runs 15, 5, then 10 mm (the spec value).
import FreeCAD as App, FreeCADGui as Gui

doc = App.getDocument(DOC)
doc.Params.set("B2", RISE); doc.recompute()
v = Gui.ActiveDocument.ActiveView; v.viewFront(); Gui.SendMsgToActiveView("ViewFit")
for _ in range(4):
    Gui.SendMsgToActiveView("ZoomIn")
print("rise", RISE, "-> top surface z", round(doc.TopSheet.Shape.BoundBox.ZMax, 3), "mm")
