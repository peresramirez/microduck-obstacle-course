# E1 gentle hump, FreeCAD step 3/4: pad the profile symmetrically to Params.width.
# Vars: DOC.
import FreeCAD as App, FreeCADGui as Gui

doc = App.getDocument(DOC); body = doc.Body; sk = doc.Profile
pad = body.newObject("PartDesign::Pad", "Hump")
pad.Profile = sk; pad.Midplane = True
pad.setExpression("Length", "Params.width")
sk.Visibility = False
doc.recompute()
pad.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=(0.86, 0.74, 0.55))]
s = body.Shape; b = s.BoundBox
print("valid", s.isValid(), "solids", len(s.Solids), "volume_l", round(s.Volume / 1e6, 3),
      "bbox", [round(x, 3) for x in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
