# F floor and lane, FreeCAD step 1/3: new document with the Params spreadsheet.
# Vars (apps.py --var): DOC = document name.
import FreeCAD as App, FreeCADGui as Gui

assert DOC not in App.listDocuments(), f"document {DOC} is already open; close it or pick another DOC"
doc = App.newDocument(DOC)
doc.Label = DOC.replace("_", " ")
sh = doc.addObject("Spreadsheet::Sheet", "Params")
rows = [("length", "6000 mm", "lane length (x), layout.json floor w"),
        ("width", "1200 mm", "lane width (y), layout.json floor d"),
        ("start_line_x", "400 mm", "centre of the start tape (route start in layout.json)"),
        ("finish_line_x", "5600 mm", "centre of the finish tape (finish area in layout.json)"),
        ("tape_width", "50 mm", "white tape, painted into the floor texture (no geometry)"),
        ("friction", "1.0", "ground plane physics material in Isaac Sim (reference only)")]
sh.set("A1", "parameter"); sh.set("B1", "value"); sh.set("C1", "note")
for i, (name, val, note) in enumerate(rows, start=2):
    sh.set(f"A{i}", name); sh.set(f"B{i}", val); sh.set(f"C{i}", note)
    sh.setAlias(f"B{i}", name)
sh.setStyle("A1:C1", "bold")
sh.setColumnWidth("C", 420)
doc.recompute()
sh.ViewObject.doubleClicked()          # open the sheet so it shows on camera
print("params", {n: str(getattr(sh, n)) for n, *_ in rows})
