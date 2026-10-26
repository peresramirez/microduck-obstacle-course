# E1 gentle hump, optional on-camera demo: change Params.crest and let the solid rebuild.
# Vars: DOC, CREST (e.g. "44 mm"). build.sh runs it with 44, 10, then 33 mm (the spec value).
import FreeCAD as App, FreeCADGui as Gui

doc = App.getDocument(DOC)
doc.Params.set("B4", CREST); doc.recompute()
v = Gui.ActiveDocument.ActiveView; v.viewFront(); Gui.SendMsgToActiveView("ViewFit")
for _ in range(4):
    Gui.SendMsgToActiveView("ZoomIn")
print("crest", CREST, "-> zmax", round(doc.Body.Shape.BoundBox.ZMax, 3))
