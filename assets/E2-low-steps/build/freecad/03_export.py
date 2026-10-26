# E2 low steps, FreeCAD step 3/3: save model.FCStd, export model.step (both sheets as one assembly) and one
# mesh per sheet for Blender, then read the STEP back. Vars: DOC, OUT (asset folder, absolute path).
import os
import FreeCAD as App, FreeCADGui as Gui, Part, MeshPart, Import

doc = App.getDocument(DOC)
os.makedirs(OUT, exist_ok=True)
assert abs(doc.TopSheet.Shape.BoundBox.ZMax - 20.0) < 1e-6, "rise is not the spec value 10 mm"
doc.saveAs(os.path.join(OUT, "model.FCStd"))
Import.export([doc.LowSteps], os.path.join(OUT, "model.step"))
for name, stl in (("BottomSheet", "freecad-mesh-bottom.stl"), ("TopSheet", "freecad-mesh-top.stl")):
    m = MeshPart.meshFromShape(Shape=doc.getObject(name).Shape, LinearDeflection=0.1, AngularDeflection=0.0873, Relative=False)
    m.write(os.path.join(OUT, stl))                    # mm; Blender imports at 0.001
    print("mesh", stl, "triangles", m.CountFacets, "solid", m.isSolid())
s = Part.read(os.path.join(OUT, "model.step")); b = s.BoundBox
print("step: valid", s.isValid(), "solids", len(s.Solids), "volumes_l", sorted(round(x.Volume / 1e6, 4) for x in s.Solids),
      "bbox_mm", [round(x, 3) for x in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
