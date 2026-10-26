# E3 wet floor, FreeCAD step 1/3: new document with the Params spreadsheet.
# Geometry is a thin tile; friction is recorded here too (it is applied in Isaac Sim, not FreeCAD).
# Vars (apps.py --var): DOC = document name.
import FreeCAD as App, FreeCADGui as Gui

assert DOC not in App.listDocuments(), f"document {DOC} is already open; close it or pick another DOC"
doc = App.newDocument(DOC)
doc.Label = DOC.replace("_", " ")
sh = doc.addObject("Spreadsheet::Sheet", "Params")
rows = [("length", "800 mm", "tile length along the lane (x)"),
        ("width", "600 mm", "tile width across the lane (y)"),
        ("thickness", "2 mm", "thin enough not to be a step, thick enough to have its own collider"),
        ("friction", "0.3", "static and dynamic friction (physics material in Isaac Sim; training 0.2-1.2)")]
sh.set("A1", "parameter"); sh.set("B1", "value"); sh.set("C1", "note")
for i, (name, val, note) in enumerate(rows, start=2):
    sh.set(f"A{i}", name); sh.set(f"B{i}", val); sh.set(f"C{i}", note)
    sh.setAlias(f"B{i}", name)
sh.setStyle("A1:C1", "bold")
sh.setColumnWidth("C", 420)
doc.recompute()
sh.ViewObject.doubleClicked()          # open the sheet so it shows on camera
print("params length", sh.length, "width", sh.width, "thickness", sh.thickness, "friction", sh.friction)
