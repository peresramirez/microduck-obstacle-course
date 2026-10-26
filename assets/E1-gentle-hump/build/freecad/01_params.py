# E1 gentle hump, FreeCAD step 1/4: new document with the Params spreadsheet.
# Vars (apps.py --var): DOC = document name.
import FreeCAD as App, FreeCADGui as Gui

assert DOC not in App.listDocuments(), f"document {DOC} is already open; close it or pick another DOC"
doc = App.newDocument(DOC)
doc.Label = DOC.replace("_", " ")
sh = doc.addObject("Spreadsheet::Sheet", "Params")
rows = [("length", "1000 mm", "hump length along the lane (x)"),
        ("width", "600 mm", "hump width across the lane (y)"),
        ("crest", "33 mm", "crest height; max slope = pi*crest/length (5.9 deg)")]
sh.set("A1", "parameter"); sh.set("B1", "value"); sh.set("C1", "note")
for i, (name, val, note) in enumerate(rows, start=2):
    sh.set(f"A{i}", name); sh.set(f"B{i}", val); sh.set(f"C{i}", note)
    sh.setAlias(f"B{i}", name)
sh.set("A6", "segments"); sh.set("B6", "32"); sh.set("C6", "profile polyline segments (fixed)")
sh.setStyle("A1:C1", "bold")
sh.setColumnWidth("C", 380)
doc.recompute()
sh.ViewObject.doubleClicked()          # open the sheet so it shows on camera
print("params", sh.length, sh.width, sh.crest)
