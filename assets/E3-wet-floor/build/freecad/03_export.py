# E3 wet floor, FreeCAD step 3/3: save model.FCStd, export model.step and the mesh for Blender, read the STEP back.
# Vars: DOC, OUT (asset folder, absolute path).
import os
import FreeCAD as App, FreeCADGui as Gui, Part, MeshPart, Import

doc = App.getDocument(DOC)
os.makedirs(OUT, exist_ok=True)
assert abs(doc.Tile.Shape.BoundBox.ZMax - 2.0) < 1e-6, "thickness is not the spec value 2 mm"
doc.saveAs(os.path.join(OUT, "model.FCStd"))
Import.export([doc.WetFloor], os.path.join(OUT, "model.step"))
m = MeshPart.meshFromShape(Shape=doc.Tile.Shape, LinearDeflection=0.1, AngularDeflection=0.0873, Relative=False)
m.write(os.path.join(OUT, "freecad-mesh.stl"))          # mm; Blender imports at 0.001
s = Part.read(os.path.join(OUT, "model.step")); b = s.BoundBox
print("step: valid", s.isValid(), "solids", len(s.Solids), "volume_l", round(s.Volume / 1e6, 4),
      "bbox_mm", [round(x, 3) for x in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
print("mesh: triangles", m.CountFacets, "solid", m.isSolid())
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
