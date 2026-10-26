# E4 box, FreeCAD step 1/3: new document with the Params spreadsheet.
# Vars (apps.py --var): DOC = document name.
import FreeCAD as App, FreeCADGui as Gui

assert DOC not in App.listDocuments(), f"document {DOC} is already open; close it or pick another DOC"
doc = App.newDocument(DOC)
doc.Label = DOC.replace("_", " ")
sh = doc.addObject("Spreadsheet::Sheet", "Params")
rows = [("length", "200 mm", "along the lane (x)"),
        ("width", "200 mm", "across the lane (y)"),
        ("height", "150 mm", "training range 100-200 mm; always below the 250 mm duck"),
        ("wall", "12 mm", "plywood thickness"),
        ("hole_length", "90 mm", "hand-hole slot, overall length"),
        ("hole_height", "30 mm", "hand-hole slot height (= end radius x 2)"),
        ("hole_top_offset", "30 mm", "from the box top down to the slot"),
        ("friction", "0.8", "physics material in Isaac Sim (reference only)")]
sh.set("A1", "parameter"); sh.set("B1", "value"); sh.set("C1", "note")
for i, (name, val, note) in enumerate(rows, start=2):
    sh.set(f"A{i}", name); sh.set(f"B{i}", val); sh.set(f"C{i}", note)
    sh.setAlias(f"B{i}", name)
sh.setStyle("A1:C1", "bold")
sh.setColumnWidth("C", 400)
doc.recompute()
sh.ViewObject.doubleClicked()          # open the sheet so it shows on camera
print("params", {n: str(getattr(sh, n)) for n, *_ in rows})
