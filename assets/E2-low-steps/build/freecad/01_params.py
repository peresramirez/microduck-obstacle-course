# E2 low steps, FreeCAD step 1/3: new document with the Params spreadsheet.
# Vars (apps.py --var): DOC = document name.
import FreeCAD as App, FreeCADGui as Gui

assert DOC not in App.listDocuments(), f"document {DOC} is already open; close it or pick another DOC"
doc = App.newDocument(DOC)
doc.Label = DOC.replace("_", " ")
sh = doc.addObject("Spreadsheet::Sheet", "Params")
rows = [("rise", "10 mm", "height of each step = plywood sheet thickness"),
        ("tread", "200 mm", "bottom sheet visible before and after the top sheet"),
        ("top_length", "800 mm", "top sheet length along the lane (x)"),
        ("width", "600 mm", "both sheets, across the lane (y)"),
        ("bottom_length", "=top_length + 2 * tread", "derived: bottom sheet length (1200 mm)")]
sh.set("A1", "parameter"); sh.set("B1", "value"); sh.set("C1", "note")
for i, (name, val, note) in enumerate(rows, start=2):
    sh.set(f"A{i}", name); sh.set(f"B{i}", val); sh.set(f"C{i}", note)
    sh.setAlias(f"B{i}", name)
sh.setStyle("A1:C1", "bold")
sh.setColumnWidth("C", 380)
doc.recompute()
sh.ViewObject.doubleClicked()          # open the sheet so it shows on camera
print("params rise", sh.rise, "tread", sh.tread, "top", sh.top_length, "width", sh.width, "bottom", sh.bottom_length)
