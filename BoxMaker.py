import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
import Part
import math
import common

RIM_WIDTH = 1.0  # Width of the rim that holds the lid in place

class BoxParameters:
    def __init__(self, outer_l, outer_w, outer_h,
                 outer_sides_fillet_enabled, outer_sides_fillet_r,
                 outer_top_fillet_enabled, outer_top_fillet_r,
                 chamfer_enabled, chamfer_s,
                 lid_enabled, clearance, lid_thickness):
        self.outer_l = outer_l
        self.outer_w = outer_w
        self.outer_h = outer_h
        self.outer_sides_fillet_enabled = outer_sides_fillet_enabled
        self.outer_sides_fillet_r = outer_sides_fillet_r
        self.outer_top_fillet_enabled = outer_top_fillet_enabled
        self.outer_top_fillet_r = outer_top_fillet_r
        self.chamfer_enabled = chamfer_enabled
        self.chamfer_s = chamfer_s
        self.lid_enabled = lid_enabled
        self.clearance = clearance
        self.lid_thickness = lid_thickness

class BoxMakerDialog(QtGui.QDialog):
    def __init__(self):
        super(BoxMakerDialog, self).__init__()
        self.initUI()
        
    def initUI(self):
        # Set up the window title and layout
        self.setWindowTitle("Create New Box")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.mainLayout = QtGui.QGridLayout(self)
        
        # --- Outer Dimensions Group Box ---
        outerGroupBox = QtGui.QGroupBox("Outer Dimensions", self)
        outerLayout = QtGui.QGridLayout(outerGroupBox)
        
        # Outer Length
        outerLengthLabel = QtGui.QLabel("Length:", self)
        self.outerLengthEdit = QtGui.QLineEdit(self)
        self.outerLengthEdit.setText("95.0")
        outerLayout.addWidget(outerLengthLabel, 0, 0)
        outerLayout.addWidget(self.outerLengthEdit, 0, 1)
        
        # Outer Width
        outerWidthLabel = QtGui.QLabel("Width:", self)
        self.outerWidthEdit = QtGui.QLineEdit(self)
        self.outerWidthEdit.setText("68.5")
        outerLayout.addWidget(outerWidthLabel, 1, 0)
        outerLayout.addWidget(self.outerWidthEdit, 1, 1)
        
        # Outer Height
        outerHeightLabel = QtGui.QLabel("Height:", self)
        self.outerHeightEdit = QtGui.QLineEdit(self)
        self.outerHeightEdit.setText("34.0")
        outerLayout.addWidget(outerHeightLabel, 2, 0)
        outerLayout.addWidget(self.outerHeightEdit, 2, 1)
        
        self.mainLayout.addWidget(outerGroupBox, 0, 0)
        
        # --- Outer Fillet & Chamfer Options Group Box ---
        outerOptionsGroupBox = QtGui.QGroupBox("Outer Fillet & Chamfer Options", self)
        outerOptionsLayout = QtGui.QGridLayout(outerOptionsGroupBox)
        
        # Fillet sides option
        self.outerSidesFilletCheck = QtGui.QCheckBox("Fillet outer vertical corners", self)
        self.outerSidesFilletCheck.setChecked(True)
        outerOptionsLayout.addWidget(self.outerSidesFilletCheck, 0, 0)
        
        outerSidesFilletRadiusLabel = QtGui.QLabel("Side Radius:", self)
        self.outerSidesFilletRadiusEdit = QtGui.QLineEdit(self)
        self.outerSidesFilletRadiusEdit.setText("3.0")
        outerOptionsLayout.addWidget(outerSidesFilletRadiusLabel, 0, 1)
        outerOptionsLayout.addWidget(self.outerSidesFilletRadiusEdit, 0, 2)
        
        # Fillet top option
        self.outerTopFilletCheck = QtGui.QCheckBox("Fillet outer top edges", self)
        self.outerTopFilletCheck.setChecked(False)
        outerOptionsLayout.addWidget(self.outerTopFilletCheck, 1, 0)
        
        outerTopFilletRadiusLabel = QtGui.QLabel("Top Radius:", self)
        self.outerTopFilletRadiusEdit = QtGui.QLineEdit(self)
        self.outerTopFilletRadiusEdit.setText("1.0")
        outerOptionsLayout.addWidget(outerTopFilletRadiusLabel, 1, 1)
        outerOptionsLayout.addWidget(self.outerTopFilletRadiusEdit, 1, 2)
        
        # Chamfer option
        self.chamferCheck = QtGui.QCheckBox("Chamfer bottom edge (30°)", self)
        self.chamferCheck.setChecked(True)
        outerOptionsLayout.addWidget(self.chamferCheck, 2, 0)
        
        chamferSizeLabel = QtGui.QLabel("Chamfer Size:", self)
        self.chamferSizeEdit = QtGui.QLineEdit(self)
        self.chamferSizeEdit.setText("1.0")
        outerOptionsLayout.addWidget(chamferSizeLabel, 2, 1)
        outerOptionsLayout.addWidget(self.chamferSizeEdit, 2, 2)
        
        self.mainLayout.addWidget(outerOptionsGroupBox, 1, 0)
        
        # --- Lid Options Group Box ---
        lidOptionsGroupBox = QtGui.QGroupBox("Lid Options", self)
        lidOptionsLayout = QtGui.QGridLayout(lidOptionsGroupBox)
        
        self.lidCheck = QtGui.QCheckBox("Create a lid", self)
        self.lidCheck.setChecked(True)
        lidOptionsLayout.addWidget(self.lidCheck, 0, 0)
        
        lidThicknessLabel = QtGui.QLabel("Lid Thickness:", self)
        self.lidThicknessEdit = QtGui.QLineEdit(self)
        self.lidThicknessEdit.setText("2.0")
        lidOptionsLayout.addWidget(lidThicknessLabel, 1, 0)
        lidOptionsLayout.addWidget(self.lidThicknessEdit, 1, 1)
        
        clearanceLabel = QtGui.QLabel("Clearance:", self)
        self.clearanceEdit = QtGui.QLineEdit(self)
        self.clearanceEdit.setText("0.1")
        lidOptionsLayout.addWidget(clearanceLabel, 2, 0)
        lidOptionsLayout.addWidget(self.clearanceEdit, 2, 1)
        
        self.mainLayout.addWidget(lidOptionsGroupBox, 5, 0)
        
        # --- Buttons ---
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, self)
        self.mainLayout.addWidget(buttonBox, 6, 0)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
    def getValues(self):
        try:
            # Parse the input values from the text fields
            outer_l = float(self.outerLengthEdit.text())
            outer_w = float(self.outerWidthEdit.text())
            outer_h = float(self.outerHeightEdit.text())
            
            outer_sides_fillet_enabled = self.outerSidesFilletCheck.isChecked()
            outer_top_fillet_enabled = self.outerTopFilletCheck.isChecked()
            chamfer_enabled = self.chamferCheck.isChecked()
            lid_enabled = self.lidCheck.isChecked()
            
            outer_sides_fillet_r = 0.0
            outer_top_fillet_r = 0.0
            chamfer_s = 0.0
            clearance = 0.0
            lid_thickness = 0.0
            
            if outer_sides_fillet_enabled:
                outer_sides_fillet_r = float(self.outerSidesFilletRadiusEdit.text())
            if outer_top_fillet_enabled:
                outer_top_fillet_r = float(self.outerTopFilletRadiusEdit.text())
            if chamfer_enabled:
                chamfer_s = float(self.chamferSizeEdit.text())
            if lid_enabled:
                clearance = float(self.clearanceEdit.text())
                lid_thickness = float(self.lidThicknessEdit.text())
            
            # Basic input validation
            if outer_l <= 0 or outer_w <= 0 or outer_h <= 0:
                QtGui.QMessageBox.critical(self, "Input Error", "All dimensions must be greater than zero.")
                return None
            
            if outer_sides_fillet_enabled and outer_sides_fillet_r <= 0:
                QtGui.QMessageBox.critical(self, "Input Error", "Outer sides fillet radius must be greater than zero.")
                return None
            
            if outer_top_fillet_enabled and outer_top_fillet_r <= 0:
                QtGui.QMessageBox.critical(self, "Input Error", "Outer top fillet radius must be greater than zero.")
                return None
            
            if chamfer_enabled and chamfer_s <= 0:
                QtGui.QMessageBox.critical(self, "Input Error", "Chamfer size must be greater than zero.")
                return None
            
            if lid_enabled and (clearance <= 0 or lid_thickness <= 0):
                QtGui.QMessageBox.critical(self, "Input Error", "Lid clearance and thickness must be greater than zero.")
                return None
            
            return BoxParameters(outer_l, outer_w, outer_h,
                                 outer_sides_fillet_enabled, outer_sides_fillet_r,
                                 outer_top_fillet_enabled, outer_top_fillet_r,
                                 chamfer_enabled, chamfer_s,
                                 lid_enabled, clearance, lid_thickness)
                   
        except ValueError:
            QtGui.QMessageBox.critical(self, "Input Error", "Please enter valid numbers for all dimensions.")
            return None

def create_lid(params, tool=False):
    """
    Creates a lid for the hollow box with a beveled base for a secure fit.
    
    Args:
        params (BoxParameters): The parameters from the dialog.
        tool (Boolean): Whether to size the lid as a cutting tool.
    """
    # Create the main body of the lid
    #currently the rim that holds the lid in place is 1mm wide
    lid_l = params.outer_l - 1*RIM_WIDTH
    lid_w = params.outer_w - 2*RIM_WIDTH
    lid_h = params.lid_thickness
    if not tool:
        lid_l -= 2 * params.clearance
        lid_w -= 2 * params.clearance
    
    lid_body = Part.makeBox(lid_l, lid_w, lid_h)
    
    # Chamfer the top edges to create the beveled edge
    chamfer_d1 = params.lid_thickness - .01
    chamfer_d2 = chamfer_d1 / math.sqrt(3)
    
    bevel_edges_to_chamfer = []
    for edge in lid_body.Edges:
        if math.isclose(edge.Vertexes[0].Point.z, params.lid_thickness) and math.isclose(edge.Vertexes[1].Point.z, params.lid_thickness):
            bevel_edges_to_chamfer.append(edge)
    try:
        chamfered_bevel = lid_body.makeChamfer(chamfer_d1, chamfer_d2, bevel_edges_to_chamfer[1:])
    except Exception as e:
        FreeCAD.Console.PrintError("Failed to create chamfered bevel on the lid. Clearance may be too large.")
        print(str(e))
        return
    
    return chamfered_bevel

class BoxMaker:
    def GetResources(self):
        return {
            'MenuText': 'New Box',
            'ToolTip': 'Create a parametric box',
            'Pixmap': ''  # path to icon if available
        }

    def Activated(self):
        dialog = BoxMakerDialog()
        if dialog.exec_() == QtGui.QDialog.Accepted:
            params = dialog.getValues()
            if params:
                doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()
                # Create the outer box
                outer_box_part = Part.makeBox(params.outer_l, params.outer_w, params.outer_h)
                
                # Apply fillet and chamfer operations if enabled
                if params.chamfer_enabled:
                    outer_box_part = common.chamfer_bottom(outer_box_part, params.chamfer_s)
                
                if params.outer_sides_fillet_enabled:
                    outer_box_part = common.fillet_edges(outer_box_part, params.outer_sides_fillet_r, "sides")
                
                if params.outer_top_fillet_enabled:
                    outer_box_part = common.fillet_edges(outer_box_part, params.outer_top_fillet_r, "top")
                
                # Create a new object in the document
                outer_box_obj = doc.addObject("Part::Feature", "Box")
                outer_box_obj.Shape = outer_box_part
                
                # Add the lid if enabled
                if params.lid_enabled:
                    lid = create_lid(params)
                    if lid is not None:
                        lid_obj = doc.addObject("Part::Feature", "Lid")
                        lid_obj.Shape = lid
                        lid_obj.Placement.Base = FreeCAD.Vector(0, params.outer_w + 2, 0)
                    cutter = create_lid(params, tool=True)
                    if cutter is not None:
                        cut_obj = doc.addObject("Part::Feature", "LidCut")
                        cut_obj.Shape = cutter
                        cut_obj.Placement.Base = FreeCAD.Vector(0, RIM_WIDTH, params.outer_h - 2)
                        hollow_box_w_lid = doc.addObject("Part::Cut", "HollowBoxWLid")
                        hollow_box_w_lid.Base = outer_box_obj
                        hollow_box_w_lid.Tool = cut_obj
                        hollow_box = hollow_box_w_lid
                
                # Recompute the document to show the result
                doc.recompute()
                FreeCADGui.SendMsgToActiveView("ViewFit")


    def IsActive(self):
        return True

FreeCADGui.addCommand("Make_Box_Command", BoxMaker())
