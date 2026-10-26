# E1 gentle hump, FreeCAD step 4/4: save model.FCStd, export model.step and the mesh for Blender,
# then read the STEP back to check it. Vars: DOC, OUT (asset folder, absolute path).
import os
import FreeCAD as App, FreeCADGui as Gui, Part, MeshPart, Import

doc = App.getDocument(DOC); body = doc.Body
os.makedirs(OUT, exist_ok=True)
assert abs(doc.Body.Shape.BoundBox.ZMax - 33.0) < 1e-6, "crest is not the spec value 33 mm"
doc.saveAs(os.path.join(OUT, "model.FCStd"))
Import.export([body], os.path.join(OUT, "model.step"))
m = MeshPart.meshFromShape(Shape=body.Shape, LinearDeflection=0.1, AngularDeflection=0.0873, Relative=False)
m.write(os.path.join(OUT, "freecad-mesh.stl"))          # mm; Blender imports it at 0.001
s = Part.read(os.path.join(OUT, "model.step")); b = s.BoundBox
print("step: valid", s.isValid(), "solids", len(s.Solids), "volume_l", round(s.Volume / 1e6, 4),
      "bbox_mm", [round(x, 3) for x in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
print("mesh: triangles", m.CountFacets, "points", m.CountPoints, "solid", m.isSolid())
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
