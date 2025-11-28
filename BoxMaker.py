import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
import Part
import math
import common

RIM_WIDTH = FreeCAD.Units.Quantity("1 mm")

def create_lid(L, W, H, clearance):
    """
    Creates a lid  shape
    
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

def update_compartment_zoffsets(obj):
    """
    updates the zoffsets of all compartments in the insert based on the box height
    
    Args:
        insert (InsertFeature): parent object
    """
    box = get_box(obj)
    if box is None or not hasattr(box, "Compartments"):
        return
    for comp in box.Compartments:
        if hasattr(comp, "ZOffset"):
            comp.ZOffset = box.Height - box.LidThickness

def add_lid(obj):
    """
    adds the lid object to the insert
    
    Args:
        insert (InsertFeature): parent object
    """
    lid = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Lid")
    LidFeature(lid)
    obj.addObject(lid)
    lid.Length = obj.Length
    lid.Width = obj.Width
    lid.Thickness = obj.LidThickness
    lid.Clearance = obj.Clearance
    lid.Placement.Base.x = obj.Length + FreeCAD.Units.Quantity("2 mm")
    lid.touch()

def get_lid(obj):
    for child in obj.Group:
        if child.Name.startswith("Lid"):
            return child
    return None

def get_box(obj):
    for child in obj.Group:
        if child.Name == "Box":
            return child
    return None

class ViewProviderBGIW:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj, mode):
        return None

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return True

# ---------------- Lid ----------------
class LidFeature:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLength", "Length", "Size", "Length").Length = 95.0
        obj.addProperty("App::PropertyLength", "Width", "Size", "Width").Width = 68.5
        obj.addProperty("App::PropertyLength", "Thickness", "Size", "Thickness").Thickness = 34.0
        obj.addProperty("App::PropertyLength", "Clearance", "Clearance", "Clearance").Clearance = .1
        obj.addProperty("App::PropertyLinkList", "Labels", "Options", "Labels")
        obj.ViewObject.Proxy = ViewProviderBGIW(obj.ViewObject)

    def execute(self, obj):
        gap = FreeCAD.Units.Quantity("2 mm")
        lid = create_lid(obj.Length, obj.Width, obj.Thickness, obj.Clearance)
        for labl in obj.Labels:
            if labl.Shape is not None and not labl.Shape.isNull():
                lid = lid.cut(labl.Shape)
        obj.Shape = lid
        if obj.Shape is None:
            FreeCAD.Console.PrintError("Lid shape is None. Check parameters.\n")

# ---------------- Box ----------------
class BoxFeature:
    def __init__(self, obj):
        obj.Proxy = self
        obj.ViewObject.Proxy = ViewProviderBGIW(obj.ViewObject)
        # Add parametric properties
        obj.addProperty("App::PropertyLength", "Length", "Box", "Outer length").Length = 95.0
        obj.addProperty("App::PropertyLength", "Width", "Box", "Outer width").Width = 68.5
        obj.addProperty("App::PropertyLength", "Height", "Box", "Outer height").Height = 34.0
        obj.addProperty("App::PropertyLength", "ChamferSize", "Options", "Chamfer size").ChamferSize = 1.0
        obj.addProperty("App::PropertyLength", "FilletRadius", "Options", "Fillet radius").FilletRadius = 3.0
        obj.addProperty("App::PropertyLength", "TopFilletRadius", "Options", "Top fillet radius").TopFilletRadius = 0.0
        obj.addProperty("App::PropertyLength", "LidThickness", "Options", "Lid thickness").LidThickness = 2.0
        obj.addProperty("App::PropertyLinkList", "Compartments", "Box", "Compartments")
        obj.addProperty("App::PropertyLinkList", "Labels", "Options", "Labels")

    def execute(self, obj):
        # Rebuild geometry based on properties
        # Create the outer box
        box = Part.makeBox(obj.Length, obj.Width, obj.Height)
        # Apply fillet and chamfer operations if enabled
        if obj.ChamferSize > 0:
            box = common.chamfer_bottom(box, obj.ChamferSize)
        if obj.FilletRadius > 0:
            box = common.fillet_edges(box, obj.FilletRadius, "sides")
        if obj.TopFilletRadius > 0:
            box = common.fillet_edges(box, obj.TopFilletRadius, "top")
        
        # Cut out the lid if enabled
        if obj.LidThickness > 0:
            cutter = create_lid(obj.Length, obj.Width, obj.LidThickness, FreeCAD.Units.Quantity("0 mm"))
            if cutter is None:
                FreeCAD.Console.PrintError("Failed to create lid. Check clearance and dimensions.\n")
                return
            cutter.translate(FreeCAD.Vector(0, RIM_WIDTH, obj.Height - obj.LidThickness))
            box = box.cut(cutter)
        
        # Subtract compartments or labels if any
        for comp in obj.Compartments:
            if comp.Shape:
                box = box.cut(comp.Shape)
        for labl in obj.Labels:
            if labl.Shape is not None and not labl.Shape.isNull():
                box = box.cut(labl.Shape)
        obj.Shape = box
        if obj.Shape is None:
            FreeCAD.Console.PrintError("Box shape is None. Check parameters.\n")

# ---------------- Assembly ----------------
class InsertFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # Add parametric properties
        obj.addProperty("App::PropertyLength", "Length", "Box", "Outer length").Length = 95.0
        obj.addProperty("App::PropertyLength", "Width", "Box", "Outer width").Width = 68.5
        obj.addProperty("App::PropertyLength", "Height", "Box", "Outer height").Height = 34.0
        obj.addProperty("App::PropertyLength", "ChamferSize", "Options", "Chamfer size").ChamferSize = 1.0
        obj.addProperty("App::PropertyLength", "FilletRadius", "Options", "Fillet radius").FilletRadius = 3.0
        obj.addProperty("App::PropertyLength", "TopFilletRadius", "Options", "Top fillet radius").TopFilletRadius = 1.0
        obj.addProperty("App::PropertyBool", "HasLid", "Options", "Create lid").HasLid = True
        obj.addProperty("App::PropertyLength", "LidThickness", "Options", "Lid thickness").LidThickness = 2.0
        obj.addProperty("App::PropertyLength", "Clearance", "Options", "Clearance for lid").Clearance = 0.1

    def onChanged(self, obj, prop):
        lid = get_lid(obj)
        if hasattr(obj, "HasLid") and hasattr(obj, "Clearance"): #clearance prevents adding the lid before those props exist
            if lid and obj.HasLid == False:
                FreeCAD.ActiveDocument.removeObject(lid.Name)
                lid = None
                update_compartment_zoffsets(obj)
            elif lid == None and obj.HasLid:
                add_lid(obj)
                update_compartment_zoffsets(obj)
        else:
            return
        if lid and prop in ["Length", "Width", "HasLid", "LidThickness", "Clearance"]:
            if prop == "Length":
                lid.Length = obj.Length
            elif prop == "Width":
                lid.Width = obj.Width
            elif prop == "LidThickness":
                lid.Thickness = obj.LidThickness
            elif prop == "Clearance":
                lid.Clearance = obj.Clearance
            lid.touch()
            update_compartment_zoffsets(obj)
        box = get_box(obj)
        if box and prop in ["Length", "Width", "Height", "ChamferSize", "FilletRadius", "TopFilletRadius", "HasLid", "LidThickness"]:
            if prop == "Length":
                box.Length = obj.Length
            elif prop == "Width":
                box.Width = obj.Width
            elif prop == "Height":
                box.Height = obj.Height
            elif prop == "ChamferSize":
                box.ChamferSize = obj.ChamferSize
            elif prop == "FilletRadius":
                box.FilletRadius = obj.FilletRadius
            elif prop == "TopFilletRadius":
                box.TopFilletRadius = obj.TopFilletRadius
            elif prop == "LidThickness":
                if obj.HasLid:
                    box.LidThickness = obj.LidThickness
                else:
                    box.LidThickness = 0
            box.touch()


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
        outerSidesFilletRadiusLabel = QtGui.QLabel("Side Radius:", form)
        self.outerSidesFilletRadiusEdit = QtGui.QDoubleSpinBox(form)
        self.outerSidesFilletRadiusEdit.setValue(obj.FilletRadius)
        outerOptionsLayout.addWidget(outerSidesFilletRadiusLabel, 0, 1)
        outerOptionsLayout.addWidget(self.outerSidesFilletRadiusEdit, 0, 2)
        
        # Fillet top option
        outerTopFilletRadiusLabel = QtGui.QLabel("Top Radius:", form)
        self.outerTopFilletRadiusEdit = QtGui.QDoubleSpinBox(form)
        self.outerTopFilletRadiusEdit.setValue(obj.TopFilletRadius)
        outerOptionsLayout.addWidget(outerTopFilletRadiusLabel, 1, 1)
        outerOptionsLayout.addWidget(self.outerTopFilletRadiusEdit, 1, 2)
        
        # Chamfer option
        chamferSizeLabel = QtGui.QLabel("Bottom Chamfer Size:", form)
        self.chamferSizeEdit = QtGui.QDoubleSpinBox(form)
        self.chamferSizeEdit.setValue(obj.ChamferSize)
        outerOptionsLayout.addWidget(chamferSizeLabel, 2, 1)
        outerOptionsLayout.addWidget(self.chamferSizeEdit, 2, 2)
        
        layout.addWidget(outerOptionsGroupBox)
        
        # --- Lid Options Group Box ---
        lidOptionsGroupBox = QtGui.QGroupBox("Lid Options", form)
        lidOptionsLayout = QtGui.QGridLayout(lidOptionsGroupBox)
        
        self.lidCheck = QtGui.QCheckBox("Create a lid", form)
        self.lidCheck.setChecked(obj.HasLid)
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
        
        self.obj.FilletRadius = self.outerSidesFilletRadiusEdit.value()
        self.obj.TopFilletRadius = self.outerTopFilletRadiusEdit.value()
        self.obj.ChamferSize = self.chamferSizeEdit.value()
        self.obj.LidThickness = self.lidThicknessEdit.value()
        self.obj.Clearance = self.clearanceEdit.value()
        
        #and children
        lid = get_lid(self.obj)
        if lid and self.obj.HasLid == False:
            FreeCAD.ActiveDocument.removeObject(lid.Name)
            lid = None
            update_compartment_zoffsets(self.obj)
        elif lid == None and self.obj.HasLid:
            add_lid(self.obj)
            update_compartment_zoffsets(self.obj)
        elif lid:
            lid.Length = self.obj.Length
            lid.Width = self.obj.Width
            lid.Thickness = self.obj.LidThickness
            lid.Clearance = self.obj.Clearance
            lid.Placement.Base.x = self.obj.Length + FreeCAD.Units.Quantity("2 mm")
        box = get_box(self.obj)
        if box:
            box.Length = self.obj.Length
            box.Width = self.obj.Width
            box.Height = self.obj.Height
            box.ChamferSize = self.obj.ChamferSize
            box.FilletRadius = self.obj.FilletRadius
            box.TopFilletRadius = self.obj.TopFilletRadius
            if self.obj.HasLid:
                box.LidThickness = self.obj.LidThickness
            else:
                box.LidThickness = 0
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        return True

#---------------- workbench button ------------------
class BoxMaker:
    def GetResources(self):
        return {
            'MenuText': 'New Box',
            'ToolTip': 'Create a parametric box',
            'Pixmap': ''  # path to icon if available
        }

    def Activated(self):
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()
        insert = doc.addObject("App::DocumentObjectGroupPython", "Insert")
        InsertFeature(insert)
        box = doc.addObject("Part::FeaturePython", "Box")
        BoxFeature(box)
        insert.addObject(box)
        #lid gets created when task panel is accepted
        doc.recompute()
        FreeCADGui.Control.showDialog(BoxTaskPanel(insert))
        FreeCADGui.SendMsgToActiveView("ViewFit")



    def IsActive(self):
        return True

FreeCADGui.addCommand("Make_Box_Command", BoxMaker())
