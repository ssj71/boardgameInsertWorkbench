import FreeCADGui

class BIWorkbench (FreeCADGui.Workbench):
    def __init__(self):
        self.__class__.MenuText = "BoardgameInsert"
        self.__class__.ToolTip = "A custom workbench for creating board game inserts and organizers"
        self.__class__.Icon = ""  # path to an icon if you want

    def Initialize(self):
        import BoxMaker
        import CompartmentMaker
        self.appendToolbar("Boardgame Insert", ["Make_Box_Command", "Add_Compartment_Command"])

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(BIWorkbench())

