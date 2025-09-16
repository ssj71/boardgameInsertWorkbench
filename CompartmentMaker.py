import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
import Part
import math
import common

class CompartmentParameters:
    def __init__(self, inner_l, inner_w, inner_h,
                 inner_sides_fillet_enabled, inner_bottom_fillet_enabled,
                 inner_sides_fillet_r, inner_bottom_fillet_r,
                 finger_hole_front_enabled, finger_hole_back_enabled,
                 finger_hole_left_enabled, finger_hole_right_enabled,
                 finger_hole_bottom_enabled, finger_hole_radius):
        self.inner_l = inner_l
        self.inner_w = inner_w
        self.inner_h = inner_h
        self.inner_sides_fillet_enabled = inner_sides_fillet_enabled
        self.inner_bottom_fillet_enabled = inner_bottom_fillet_enabled
        self.inner_sides_fillet_r = inner_sides_fillet_r
        self.inner_bottom_fillet_r = inner_bottom_fillet_r
        self.finger_hole_front_enabled = finger_hole_front_enabled
        self.finger_hole_back_enabled = finger_hole_back_enabled
        self.finger_hole_left_enabled = finger_hole_left_enabled
        self.finger_hole_right_enabled = finger_hole_right_enabled
        self.finger_hole_bottom_enabled = finger_hole_bottom_enabled
        self.finger_hole_radius = finger_hole_radius

class CompartmentMakerDialog(QtGui.QDialog):
    def __init__(self):
        super(CompartmentMakerDialog, self).__init__()
        self.initUI()
        
    def initUI(self):
        # Set up the window title and layout
        self.setWindowTitle("Add Compartment")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.mainLayout = QtGui.QGridLayout(self)
        
        # --- Inner Dimensions Group Box ---
        innerGroupBox = QtGui.QGroupBox("Inner Dimensions", self)
        innerLayout = QtGui.QGridLayout(innerGroupBox)
        
        # Inner Length
        innerLengthLabel = QtGui.QLabel("Length:", self)
        self.innerLengthEdit = QtGui.QLineEdit(self)
        self.innerLengthEdit.setText("91.0")
        innerLayout.addWidget(innerLengthLabel, 0, 0)
        innerLayout.addWidget(self.innerLengthEdit, 0, 1)
        
        # Inner Width
        innerWidthLabel = QtGui.QLabel("Width:", self)
        self.innerWidthEdit = QtGui.QLineEdit(self)
        self.innerWidthEdit.setText("64.5")
        innerLayout.addWidget(innerWidthLabel, 1, 0)
        innerWidthLabel.setToolTip("Must be less than Outer Width")
        innerLayout.addWidget(self.innerWidthEdit, 1, 1)
        
        # Inner Height
        innerHeightLabel = QtGui.QLabel("Height:", self)
        self.innerHeightEdit = QtGui.QLineEdit(self)
        self.innerHeightEdit.setText("30.0")
        innerLayout.addWidget(innerHeightLabel, 2, 0)
        innerHeightLabel.setToolTip("Must be less than Outer Height")
        innerLayout.addWidget(self.innerHeightEdit, 2, 1)
        
        self.mainLayout.addWidget(innerGroupBox, 0, 0)
        
        # --- Inner Fillet Options Group Box ---
        innerOptionsGroupBox = QtGui.QGroupBox("Inner Fillet Options", self)
        innerOptionsLayout = QtGui.QGridLayout(innerOptionsGroupBox)

        # Fillet inner sides
        self.innerSidesFilletCheck = QtGui.QCheckBox("Fillet inner sides", self)
        self.innerSidesFilletCheck.setChecked(True)
        innerOptionsLayout.addWidget(self.innerSidesFilletCheck, 0, 0)

        innerSidesFilletRadiusLabel = QtGui.QLabel("Side Radius:", self)
        self.innerSidesFilletRadiusEdit = QtGui.QLineEdit(self)
        self.innerSidesFilletRadiusEdit.setText("2.0")
        innerOptionsLayout.addWidget(innerSidesFilletRadiusLabel, 0, 1)
        innerOptionsLayout.addWidget(self.innerSidesFilletRadiusEdit, 0, 2)

        # Fillet inner bottom edges
        self.innerBottomFilletCheck = QtGui.QCheckBox("Fillet inner bottom edges", self)
        self.innerBottomFilletCheck.setChecked(True)
        innerOptionsLayout.addWidget(self.innerBottomFilletCheck, 1, 0)
        
        innerBottomFilletRadiusLabel = QtGui.QLabel("Bottom Radius:", self)
        self.innerBottomFilletRadiusEdit = QtGui.QLineEdit(self)
        self.innerBottomFilletRadiusEdit.setText("2.0")
        innerOptionsLayout.addWidget(innerBottomFilletRadiusLabel, 1, 1)
        innerOptionsLayout.addWidget(self.innerBottomFilletRadiusEdit, 1, 2)

        self.mainLayout.addWidget(innerOptionsGroupBox, 1, 0)

        # --- Finger Hole Options Group Box ---
        fingerHoleGroupBox = QtGui.QGroupBox("Finger Hole Options", self)
        fingerHoleLayout = QtGui.QGridLayout(fingerHoleGroupBox)

        self.fingerHoleFrontCheck = QtGui.QCheckBox("Front", self)
        fingerHoleLayout.addWidget(self.fingerHoleFrontCheck, 0, 0)
        self.fingerHoleBackCheck = QtGui.QCheckBox("Back", self)
        fingerHoleLayout.addWidget(self.fingerHoleBackCheck, 0, 1)
        self.fingerHoleLeftCheck = QtGui.QCheckBox("Left", self)
        fingerHoleLayout.addWidget(self.fingerHoleLeftCheck, 1, 0)
        self.fingerHoleRightCheck = QtGui.QCheckBox("Right", self)
        fingerHoleLayout.addWidget(self.fingerHoleRightCheck, 1, 1)
        self.fingerHoleBottomCheck = QtGui.QCheckBox("Bottom", self)
        fingerHoleLayout.addWidget(self.fingerHoleBottomCheck, 2, 0)

        fingerHoleRadiusLabel = QtGui.QLabel("Radius:", self)
        self.fingerHoleRadiusEdit = QtGui.QLineEdit(self)
        self.fingerHoleRadiusEdit.setText("10.0")
        fingerHoleLayout.addWidget(fingerHoleRadiusLabel, 3, 0)
        fingerHoleLayout.addWidget(self.fingerHoleRadiusEdit, 3, 1)

        self.mainLayout.addWidget(fingerHoleGroupBox, 2, 0)
        
        # --- Buttons ---
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, self)
        self.mainLayout.addWidget(buttonBox, 3, 0)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
    def getValues(self):
        try:
            # Parse the input values from the text fields
            inner_l = float(self.innerLengthEdit.text())
            inner_w = float(self.innerWidthEdit.text())
            inner_h = float(self.innerHeightEdit.text())
            
            inner_sides_fillet_enabled = self.innerSidesFilletCheck.isChecked()
            inner_bottom_fillet_enabled = self.innerBottomFilletCheck.isChecked()
            finger_hole_front_enabled = self.fingerHoleFrontCheck.isChecked()
            finger_hole_back_enabled = self.fingerHoleBackCheck.isChecked()
            finger_hole_left_enabled = self.fingerHoleLeftCheck.isChecked()
            finger_hole_right_enabled = self.fingerHoleRightCheck.isChecked()
            finger_hole_bottom_enabled = self.fingerHoleBottomCheck.isChecked()
            
            inner_sides_fillet_r = 0.0
            inner_bottom_fillet_r = 0.0
            finger_hole_radius = 0.0

            if inner_sides_fillet_enabled:
                inner_sides_fillet_r = float(self.innerSidesFilletRadiusEdit.text())
            if inner_bottom_fillet_enabled:
                inner_bottom_fillet_r = float(self.innerBottomFilletRadiusEdit.text())
            if (finger_hole_front_enabled or finger_hole_back_enabled or
                finger_hole_left_enabled or finger_hole_right_enabled or
                finger_hole_bottom_enabled):
                finger_hole_radius = float(self.fingerHoleRadiusEdit.text())

            # Basic input validation
            if inner_sides_fillet_enabled and inner_sides_fillet_r <= 0:
                QtGui.QMessageBox.critical(self, "Input Error", "Inner sides fillet radius must be greater than zero.")
                return None
            
            if inner_bottom_fillet_enabled and inner_bottom_fillet_r <= 0:
                QtGui.QMessageBox.critical(self, "Input Error", "Inner bottom fillet radius must be greater than zero.")
                return None
            
            if finger_hole_radius <= 0 and (finger_hole_front_enabled or finger_hole_back_enabled or
                                             finger_hole_left_enabled or finger_hole_right_enabled or
                                             finger_hole_bottom_enabled):
                QtGui.QMessageBox.critical(self, "Input Error", "Finger hole radius must be greater than zero if any finger holes are enabled.")
                return None
            return CompartmentParameters(inner_l, inner_w, inner_h,
                                 inner_sides_fillet_enabled, inner_bottom_fillet_enabled,
                                 inner_sides_fillet_r, inner_bottom_fillet_r,
                                 finger_hole_front_enabled, finger_hole_back_enabled,
                                 finger_hole_left_enabled, finger_hole_right_enabled,
                                 finger_hole_bottom_enabled, finger_hole_radius)
        except ValueError:
            QtGui.QMessageBox.critical(self, "Input Error", "Please enter valid numbers for all dimensions.")
            return None

def create_finger_holes(params):
    """
    Cuts finger holes into the box based on user selection.
    
    Args:
        params (BoxParameters): The parameters from the dialog.
    
    Returns:
        Part.Shape: The shape to use for cutting.
    """
    
    # Finger hole cutter dimensions
    radius = params.finger_hole_radius
    height = 2*params.inner_h # A bit longer than height to ensure a clean cut
    
    # Common position for the center of the cylinder's face
    y_center = params.inner_w / 2
    x_center = params.inner_l / 2
    
    list_of_cutters = []
    
    # Front face cutout
    if params.finger_hole_front_enabled:
        cutter = Part.makeCylinder(radius, height)
        cutter.Placement.Base = App.Vector(x_center, 0, -1)
        list_of_cutters.append(cutter)
        
    # Back face cutout
    if params.finger_hole_back_enabled:
        cutter = Part.makeCylinder(radius, height)
        cutter.Placement.Base = App.Vector(x_center, params.inner_w, -1)
        list_of_cutters.append(cutter)
    
    # Left face cutout
    if params.finger_hole_left_enabled:
        cutter = Part.makeCylinder(radius, height)
        cutter.Placement.Base = App.Vector(0, y_center, -1)
        list_of_cutters.append(cutter)
    
    # Right face cutout
    if params.finger_hole_right_enabled:
        cutter = Part.makeCylinder(radius, height)
        cutter.Placement.Base = App.Vector(params.inner_l, y_center, -1)
        list_of_cutters.append(cutter)
    
    # Bottom face cutout
    if params.finger_hole_bottom_enabled:
        cutter = Part.makeCylinder(radius, height)
        cutter.Placement.Base = App.Vector(x_center, y_center, -1)
        list_of_cutters.append(cutter)
    
    return Part.makeCompound(list_of_cutters)

class CompartmentMaker:
    def GetResources(self):
        return {
            'MenuText': 'Add Compartment',
            'ToolTip': 'Put a compartment in a box',
            'Pixmap': ''  # path to icon if available
        }

    def Activated(self):
        dialog = CompartmentMakerDialog()
        if dialog.exec_() == QtGui.QDialog.Accepted:
            params = dialog.getValues()
            if params:
                doc = FreeCAD.ActiveDocument
                # Get the selected outer box
                sel = FreeCADGui.Selection.getSelection()
                if not sel or len(sel) != 1:
                    QtGui.QMessageBox.critical(None, "Selection Error", "Please select exactly one outer box.")
                    return
                outer_box_obj = sel[0]
                
                # Create the inner box
                inner_box_part = Part.makeBox(params.inner_l, params.inner_w, params.inner_h)
                
                # Find and fillet inner edges if enabled
                if params.inner_sides_fillet_enabled:
                    inner_box_part = common.fillet_edges(inner_box_part, params.inner_sides_fillet_r, "sides")
                
                if params.inner_bottom_fillet_enabled:
                    inner_box_part = common.fillet_edges(inner_box_part, params.inner_bottom_fillet_r, "bottom")
                 
                # Position the inner box to be centered within the outer box
                #TODO: placeholders
                x_pos = 2
                y_pos = 2
                z_pos = 2
                inner_box_part.Placement.Base = FreeCAD.Vector(x_pos, y_pos, z_pos)
                
                # Subtract the inner box from the outer box to create the hollow shape
                hollow_box = doc.addObject("Part::Cut", "HollowBox")
                hollow_box.Base = outer_box_obj
                hollow_box.Tool = doc.addObject("Part::Feature", "InnerBox")
                hollow_box.Tool.Shape = inner_box_part
                
                # Add finger holes if selected
                if (params.finger_hole_front_enabled or params.finger_hole_back_enabled or
                    params.finger_hole_left_enabled or params.finger_hole_right_enabled or
                    params.finger_hole_bottom_enabled):
                    
                    finger_holes = create_finger_holes(params)
                    if finger_holes is not None:
                        cut_obj = doc.addObject("Part::Feature", "HoleCut")
                        cut_obj.Shape = finger_holes
                        #TODO: placeholder
                        cut_obj.Placement.Base = FreeCAD.Vector((params.inner_l) / 2,
                                                            (params.inner_w) / 2,
                                                            0)
                        hollow_box_w_hole = doc.addObject("Part::Cut", "HollowBoxWLid")
                        hollow_box_w_hole.Base = hollow_box
                        hollow_box_w_hole.Tool = cut_obj
                        hollow_box = hollow_box_w_hole
                
                # Recompute the document to show the result
                doc.recompute()
                FreeCADGui.SendMsgToActiveView("ViewFit")


    def IsActive(self):
        return True

FreeCADGui.addCommand("Add_Compartment_Command", CompartmentMaker())

