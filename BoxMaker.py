import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
import Part
import math
import common

RIM_WIDTH = FreeCAD.Units.Quantity("1 mm")

class BoxFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # Add parametric properties
        obj.addProperty("App::PropertyLength", "Length", "Box", "Outer length").Length = 95.0
        obj.addProperty("App::PropertyLength", "Width", "Box", "Outer width").Width = 68.5
        obj.addProperty("App::PropertyLength", "Height", "Box", "Outer height").Height = 34.0
        obj.addProperty("App::PropertyBool", "Chamfer", "Options", "Chamfer bottom").Chamfer = True
        obj.addProperty("App::PropertyLength", "ChamferSize", "Options", "Chamfer size").ChamferSize = 1.0
        obj.addProperty("App::PropertyBool", "FilletSides", "Options", "Fillet sides").FilletSides = True
        obj.addProperty("App::PropertyLength", "FilletRadius", "Options", "Fillet radius").FilletRadius = 3.0
        obj.addProperty("App::PropertyBool", "FilletTop", "Options", "Fillet top").FilletTop = True
        obj.addProperty("App::PropertyLength", "TopFilletRadius", "Options", "Top fillet radius").TopFilletRadius = 1.0
        obj.addProperty("App::PropertyBool", "Lid", "Options", "Create lid").Lid = True
        obj.addProperty("App::PropertyLength", "LidThickness", "Options", "Lid thickness").LidThickness = 2.0
        obj.addProperty("App::PropertyLength", "Clearance", "Options", "Clearance for lid").Clearance = 0.1
        obj.addProperty("App::PropertyLinkList", "Compartments", "Box", "Linked compartments")

    def execute(self, obj):
        # Rebuild geometry based on properties
        # Create the outer box
        box = Part.makeBox(obj.Length, obj.Width, obj.Height)
        # Apply fillet and chamfer operations if enabled
        if obj.Chamfer:
            box = common.chamfer_bottom(box, obj.ChamferSize)
        if obj.FilletSides:
            box = common.fillet_edges(box, obj.FilletRadius, "sides")
        if obj.FilletTop:
            box = common.fillet_edges(box, obj.TopFilletRadius, "top")
        
        # Add the lid if enabled
        lid = None
        if obj.Lid:
            gap = FreeCAD.Units.Quantity("2 mm")
            lid = create_lid(obj.Length, obj.Width, obj.LidThickness, obj.Clearance)
            cutter = create_lid(obj.Length, obj.Width, obj.LidThickness, FreeCAD.Units.Quantity("0 mm"))
            if lid is None or cutter is None:
                FreeCAD.Console.PrintError("Failed to create lid. Check clearance and dimensions.\n")
                return
            lid.translate(FreeCAD.Vector(0, obj.Width + gap, 0))
            cutter.translate(FreeCAD.Vector(0, RIM_WIDTH, obj.Height - obj.LidThickness))
            box = box.cut(cutter)
        
        # Subtract compartments if any
        for comp in obj.Compartments:
            if comp.Shape:
                box = box.cut(comp.Shape)
        if lid:
            box = Part.Compound([box,lid])
        obj.Shape = box

class BoxTaskPanel:
    def __init__(self, obj):
        form = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(form)
        
        # --- Outer Dimensions Group Box ---
        outerGroupBox = QtGui.QGroupBox("Outer Dimensions", form)
        outerLayout = QtGui.QGridLayout(outerGroupBox)
        
        # Outer Length
        outerLengthLabel = QtGui.QLabel("Length:", form)
        self.outerLengthEdit = QtGui.QDoubleSpinBox(form)
        self.outerLengthEdit.setRange(0.0, 1000.0)
        self.outerLengthEdit.setValue(obj.Length)
        outerLayout.addWidget(outerLengthLabel, 0, 0)
        outerLayout.addWidget(self.outerLengthEdit, 0, 1)
        
        # Outer Width
        outerWidthLabel = QtGui.QLabel("Width:", form)
        self.outerWidthEdit = QtGui.QDoubleSpinBox(form)
        self.outerWidthEdit.setRange(0.0, 1000.0)
        self.outerWidthEdit.setValue(obj.Width)
        outerLayout.addWidget(outerWidthLabel, 1, 0)
        outerLayout.addWidget(self.outerWidthEdit, 1, 1)
        
        # Outer Height
        outerHeightLabel = QtGui.QLabel("Height:", form)
        self.outerHeightEdit = QtGui.QDoubleSpinBox(form)
        self.outerHeightEdit.setRange(0.0, 1000.0)
        self.outerHeightEdit.setValue(obj.Height)
        outerLayout.addWidget(outerHeightLabel, 2, 0)
        outerLayout.addWidget(self.outerHeightEdit, 2, 1)
        
        layout.addWidget(outerGroupBox)
        
        # --- Outer Fillet & Chamfer Options Group Box ---
        outerOptionsGroupBox = QtGui.QGroupBox("Outer Fillet & Chamfer Options", form)
        outerOptionsLayout = QtGui.QGridLayout(outerOptionsGroupBox)
        
        # Fillet sides option
        self.outerSidesFilletCheck = QtGui.QCheckBox("Fillet outer vertical corners", form)
        self.outerSidesFilletCheck.setChecked(obj.FilletSides)
        outerOptionsLayout.addWidget(self.outerSidesFilletCheck, 0, 0)
        
        outerSidesFilletRadiusLabel = QtGui.QLabel("Side Radius:", form)
        self.outerSidesFilletRadiusEdit = QtGui.QDoubleSpinBox(form)
        self.outerSidesFilletRadiusEdit.setValue(obj.FilletRadius)
        outerOptionsLayout.addWidget(outerSidesFilletRadiusLabel, 0, 1)
        outerOptionsLayout.addWidget(self.outerSidesFilletRadiusEdit, 0, 2)
        
        # Fillet top option
        self.outerTopFilletCheck = QtGui.QCheckBox("Fillet outer top edges", form)
        self.outerTopFilletCheck.setChecked(obj.FilletTop)
        outerOptionsLayout.addWidget(self.outerTopFilletCheck, 1, 0)
        
        outerTopFilletRadiusLabel = QtGui.QLabel("Top Radius:", form)
        self.outerTopFilletRadiusEdit = QtGui.QDoubleSpinBox(form)
        self.outerTopFilletRadiusEdit.setValue(obj.TopFilletRadius)
        outerOptionsLayout.addWidget(outerTopFilletRadiusLabel, 1, 1)
        outerOptionsLayout.addWidget(self.outerTopFilletRadiusEdit, 1, 2)
        
        # Chamfer option
        self.chamferCheck = QtGui.QCheckBox("Chamfer bottom edge (30°)", form)
        self.chamferCheck.setChecked(obj.Chamfer)
        outerOptionsLayout.addWidget(self.chamferCheck, 2, 0)
        
        chamferSizeLabel = QtGui.QLabel("Chamfer Size:", form)
        self.chamferSizeEdit = QtGui.QDoubleSpinBox(form)
        self.chamferSizeEdit.setValue(obj.ChamferSize)
        outerOptionsLayout.addWidget(chamferSizeLabel, 2, 1)
        outerOptionsLayout.addWidget(self.chamferSizeEdit, 2, 2)
        
        layout.addWidget(outerOptionsGroupBox)
        
        # --- Lid Options Group Box ---
        lidOptionsGroupBox = QtGui.QGroupBox("Lid Options", form)
        lidOptionsLayout = QtGui.QGridLayout(lidOptionsGroupBox)
        
        self.lidCheck = QtGui.QCheckBox("Create a lid", form)
        self.lidCheck.setChecked(obj.Lid)
        lidOptionsLayout.addWidget(self.lidCheck, 0, 0)
        
        lidThicknessLabel = QtGui.QLabel("Lid Thickness:", form)
        self.lidThicknessEdit = QtGui.QDoubleSpinBox(form)
        self.lidThicknessEdit.setValue(obj.LidThickness)
        lidOptionsLayout.addWidget(lidThicknessLabel, 1, 0)
        lidOptionsLayout.addWidget(self.lidThicknessEdit, 1, 1)
        
        clearanceLabel = QtGui.QLabel("Clearance:", form)
        self.clearanceEdit = QtGui.QDoubleSpinBox(form)
        self.clearanceEdit.setValue(obj.Clearance)
        lidOptionsLayout.addWidget(clearanceLabel, 2, 0)
        lidOptionsLayout.addWidget(self.clearanceEdit, 2, 1)
        
        layout.addWidget(lidOptionsGroupBox)

        self.form = form
        self.obj = obj

    def accept(self):
        # Push values back into object
        self.obj.Length = self.outerLengthEdit.value()
        self.obj.Width = self.outerWidthEdit.value()
        self.obj.Height = self.outerHeightEdit.value()
        
        self.obj.FilletSides = self.outerSidesFilletCheck.isChecked()
        self.obj.FilletRadius = self.outerSidesFilletRadiusEdit.value()
        self.obj.FilletTop = self.outerTopFilletCheck.isChecked()
        self.obj.TopFilletRadius = self.outerTopFilletRadiusEdit.value()
        self.obj.Chamfer = self.chamferCheck.isChecked()
        self.obj.ChamferSize = self.chamferSizeEdit.value()
        self.obj.Lid = self.lidCheck.isChecked()
        self.obj.LidThickness = self.lidThicknessEdit.value()
        self.obj.Clearance = self.clearanceEdit.value()
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        return True

def create_lid(L, W, H, clearance):
    """
    Creates a lid for the hollow box with a beveled base for a secure fit.
    
    Args:
        params (BoxParameters): The parameters from the dialog.
        tool (Boolean): Whether to size the lid as a cutting tool.
    """
    # Create the main body of the lid
    #currently the rim that holds the lid in place is 1mm wide
    lid_l = L - 1*RIM_WIDTH - 2*clearance
    lid_w = W - 2*RIM_WIDTH - 2*clearance
    lid_h = H
    
    lid_body = Part.makeBox(lid_l, lid_w, lid_h)
    
    # Chamfer the top edges to create the beveled edge
    chamfer_d1 = H - FreeCAD.Units.Quantity(".01 mm")
    chamfer_d2 = chamfer_d1 / math.sqrt(3)
    
    bevel_edges_to_chamfer = common.get_edges(lid_body, "top")
    try:
        chamfered_bevel = lid_body.makeChamfer(chamfer_d1, chamfer_d2, bevel_edges_to_chamfer[1:])
    except Exception as e:
        FreeCAD.Console.PrintError("Failed to create chamfered bevel on the lid. Clearance may be too large.")
        print(str(e))
        return
    
    return chamfered_bevel

class ViewProviderBox:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj, mode):
        if mode == 0:
            FreeCADGui.Control.showDialog(BoxTaskPanel(vobj.Object))
            return True
        return None

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return True

class BoxMaker:
    def GetResources(self):
        return {
            'MenuText': 'New Box',
            'ToolTip': 'Create a parametric box',
            'Pixmap': ''  # path to icon if available
        }

    def Activated(self):
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()
        obj = doc.addObject("Part::FeaturePython", "InsertBox")
        BoxFeature(obj)
        obj.ViewObject.Proxy = ViewProviderBox(obj.ViewObject)
        doc.recompute()
        FreeCADGui.Control.showDialog(BoxTaskPanel(obj))
        FreeCADGui.SendMsgToActiveView("ViewFit")



    def IsActive(self):
        return True

FreeCADGui.addCommand("Make_Box_Command", BoxMaker())
