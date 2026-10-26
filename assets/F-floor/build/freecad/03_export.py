# F floor and lane, FreeCAD step 3/3: save model.FCStd, export model.step (the floor face through its App::Part;
# the tape rectangles are view-only and not exported) and the mesh for Blender, then read the STEP back.
# Vars: DOC, OUT (asset folder, absolute path).
import os
import FreeCAD as App, FreeCADGui as Gui, Part, MeshPart, Import

doc = App.getDocument(DOC)
os.makedirs(OUT, exist_ok=True)
doc.saveAs(os.path.join(OUT, "model.FCStd"))
Import.export([doc.FloorPart], os.path.join(OUT, "model.step"))
m = MeshPart.meshFromShape(Shape=doc.Floor.Shape, LinearDeflection=0.1, AngularDeflection=0.0873, Relative=False)
m.write(os.path.join(OUT, "freecad-mesh.stl"))          # mm; Blender imports at 0.001
s = Part.read(os.path.join(OUT, "model.step")); b = s.BoundBox
print("step: faces", len(s.Faces), "area_m2", round(s.Area / 1e6, 4),
      "bbox_mm", [round(x, 3) for x in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
print("mesh: triangles", m.CountFacets)
Gui.ActiveDocument.ActiveView.viewIsometric(); Gui.SendMsgToActiveView("ViewFit")
