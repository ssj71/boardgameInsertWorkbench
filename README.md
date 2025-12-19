# Boardgame Insert Workbench

![screenshot](img/screenshot.png)

This is a FreeCAD 1.0 workbench designed to help design and 3d print custom inserts for board games. It provides tools to design organizers with multiple compartments for game components or individual boxes for pieces depending on your design preferrences. This could be used to create various boxes, trays and organizers, or with other fabrication techologies, but it was designed with board games and fdm printers in mind.

I roughly tried to recreate the feature set of the [Boardgame Insert Toolkit (BIT)](https://github.com/dppdppd/The-Boardgame-Insert-Toolkit) for openSCAD though there are many features there not yet implemented here (dividers, lattices, probably more). I used BIT for one design but was disappointed by the lack of fillets. I also found the syntax errors I made when using it hard to debug. Using a workbench in freeCAD allows for a WYSIWYG approach to designing inserts.

## Installation

 1. Download or clone this repository.
 2. Copy or link the "BoardgameInsertWorkbench" folder to your FreeCAD "Mod" directory. You can find the location of this directory by opening FreeCAD, going to "Edit" -> "Preferences" -> "General" -> "Macro" tab, and checking the "Macro directory" path. The "Mod" folder is usually located in the same parent directory as the "Macro" folder.
 3. Restart FreeCAD.

## Features

 * Create boxes with multiple compartments
 * Modular labels and compartments for quick re-arrangement
 * Compartment types:
    * Rectangular
    * Circular
    * N-sided polygon shapes
    * Rectangle 2 (round bottom or sideways cylinder)
 * lots of fillet options for both boxes and compartments
 * SVG or text labels with font selection, size, and placement options
 * Optional sliding lids
 * convenient compartment arrangement functions


## Useage

 1. Open FreeCAD and switch to the "Boardgame Insert" workbench from the workbench selector.
 2. Use the "Create Box" tool to create a new box for the insert adjust parameters as desired.
 3. Use the "Add Compartment" tool to add compartments to the box adjusting parameters as desired.
 4. Double click on the compartment in the tree view to move it to the desired location within the box.
 5. Repeat steps 3 and 4 as needed to add more compartments.
 6. Use the "Add Label" tool to add labels to the box or lid as desired (for lid you must select the lid specifically in the tree view before adding the label).

The defaults will create a basic deck box with a lid. With these basic tools you should be able to create a wide variety of inserts.

 * the box dimensions are the absolute outer dimensions including the lid
 * compartment depths are also accounting for he lid thickness
 * there are no checks to ensure compartments fit within the box, its  a good idea to inspect the model

## Limitations

* changing box/lid parameters can make labels get "lost" -- you may need to delete and re-add them

enjoy!
