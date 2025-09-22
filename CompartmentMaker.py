import FreeCAD, FreeCADGui
from PySide import QtGui
import Part, math, common

class CompartmentFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # Dimensions
        obj.addProperty("App::PropertyLength", "Length", "Compartment", "Length").Length = 91.0
        obj.addProperty("App::PropertyLength", "Width", "Compartment", "Width").Width = 64.5
        obj.addProperty("App::PropertyLength", "Depth", "Compartment", "Depth").Depth = 30.0
        # Fillets
        obj.addProperty("App::PropertyBool", "FilletSides", "Compartment", "Fillet sides").FilletSides = True
        obj.addProperty("App::PropertyLength", "SideFilletRadius", "Compartment", "Side fillet radius").SideFilletRadius = 2.0
        obj.addProperty("App::PropertyBool", "FilletBottom", "Compartment", "Fillet bottom").FilletBottom = True
        obj.addProperty("App::PropertyLength", "BottomFilletRadius", "Compartment", "Bottom fillet radius").BottomFilletRadius = 2.0
        # Finger holes
        obj.addProperty("App::PropertyBool", "FingerFront", "FingerHoles", "Front finger hole").FingerFront = False
        obj.addProperty("App::PropertyBool", "FingerBack", "FingerHoles", "Back finger hole").FingerBack = False
        obj.addProperty("App::PropertyBool", "FingerLeft", "FingerHoles", "Left finger hole").FingerLeft = False
        obj.addProperty("App::PropertyBool", "FingerRight", "FingerHoles", "Right finger hole").FingerRight = False
        obj.addProperty("App::PropertyBool", "FingerBottom", "FingerHoles", "Bottom finger hole").FingerBottom = False
        obj.addProperty("App::PropertyLength", "FingerRadius", "FingerHoles", "Finger hole radius").FingerRadius = 10.0
        obj.addProperty("App::PropertyLength", "ZOffset", "Compartment", "ZOffset").ZOffset = 2.0

    def execute(self, obj):
        z = obj.ZOffset - obj.Depth
        # Build the inner box
        inner = Part.makeBox(obj.Length, obj.Width, obj.Depth, FreeCAD.Vector(0,0,z))
        if obj.FilletSides:
            inner = common.fillet_edges(inner, obj.SideFilletRadius, "sides")
        if obj.FilletBottom:
            inner = common.fillet_edges(inner, obj.BottomFilletRadius, "bottom")
        
        #important distances
        y_center = obj.Width / 2
        x_center = obj.Length / 2
        
        shapes = [inner]
        
        # Add finger holes
        r = obj.FingerRadius
        h = obj.Depth * 2
        one = FreeCAD.Units.Quantity("1 mm")
        if obj.FingerFront:
            shapes.append(Part.makeCylinder(r, h, FreeCAD.Vector(x_center, 0, z-one)))
        if obj.FingerBack:
            shapes.append(Part.makeCylinder(r, h, FreeCAD.Vector(x_center, obj.Width, z-one)))
        if obj.FingerLeft:
            shapes.append(Part.makeCylinder(r, h, FreeCAD.Vector(0, y_center, z-one)))
        if obj.FingerRight:
            shapes.append(Part.makeCylinder(r, h, FreeCAD.Vector(obj.Length, y_center, z-one)))
        if obj.FingerBottom:
            shapes.append(Part.makeCylinder(r, h, FreeCAD.Vector(x_center, y_center, -one)))
        
        cutter = Part.makeCompound(shapes)
        #cutter = cutter.translate(FreeCAD.Vector(0, 0, obj.ZOffset - obj.Depth))
        obj.Shape = cutter

class CompartmentTaskPanel:
    def __init__(self, obj):
        form = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(form)
        
        dimsGroup = QtGui.QGroupBox("Dimensions")
        dimsLayout = QtGui.QGridLayout(dimsGroup)
        
        self.lSpin = QtGui.QDoubleSpinBox(); self.lSpin.setRange(0,1000); self.lSpin.setValue(obj.Length)
        self.wSpin = QtGui.QDoubleSpinBox(); self.wSpin.setRange(0,1000); self.wSpin.setValue(obj.Width)
        self.hSpin = QtGui.QDoubleSpinBox(); self.hSpin.setRange(0,1000); self.hSpin.setValue(obj.Depth)
        dimsLayout.addWidget(QtGui.QLabel("Length:"),0,0); dimsLayout.addWidget(self.lSpin,0,1)
        dimsLayout.addWidget(QtGui.QLabel("Width:"),1,0); dimsLayout.addWidget(self.wSpin,1,1)
        dimsLayout.addWidget(QtGui.QLabel("Height:"),2,0); dimsLayout.addWidget(self.hSpin,2,1)
        layout.addWidget(dimsGroup)
        
        filletGroup = QtGui.QGroupBox("Fillets")
        fLayout = QtGui.QGridLayout(filletGroup)
        self.sideCheck = QtGui.QCheckBox("Fillet sides"); self.sideCheck.setChecked(obj.FilletSides)
        self.sideRad = QtGui.QDoubleSpinBox(); self.sideRad.setValue(obj.SideFilletRadius)
        fLayout.addWidget(self.sideCheck,0,0); fLayout.addWidget(self.sideRad,0,1)
        self.bottomCheck = QtGui.QCheckBox("Fillet bottom"); self.bottomCheck.setChecked(obj.FilletBottom)
        self.bottomRad = QtGui.QDoubleSpinBox(); self.bottomRad.setValue(obj.BottomFilletRadius)
        fLayout.addWidget(self.bottomCheck,1,0); fLayout.addWidget(self.bottomRad,1,1)
        layout.addWidget(filletGroup)
        
        fingerGroup = QtGui.QGroupBox("Finger Holes")
        gLayout = QtGui.QGridLayout(fingerGroup)
        self.front = QtGui.QCheckBox("Front"); self.front.setChecked(obj.FingerFront); gLayout.addWidget(self.front,0,0)
        self.back = QtGui.QCheckBox("Back"); self.back.setChecked(obj.FingerBack); gLayout.addWidget(self.back,0,1)
        self.left = QtGui.QCheckBox("Left"); self.left.setChecked(obj.FingerLeft); gLayout.addWidget(self.left,1,0)
        self.right = QtGui.QCheckBox("Right"); self.right.setChecked(obj.FingerRight); gLayout.addWidget(self.right,1,1)
        self.bottom = QtGui.QCheckBox("Bottom"); self.bottom.setChecked(obj.FingerBottom); gLayout.addWidget(self.bottom,2,0)
        self.fingerRad = QtGui.QDoubleSpinBox(); self.fingerRad.setValue(obj.FingerRadius)
        gLayout.addWidget(QtGui.QLabel("Radius:"),3,0); gLayout.addWidget(self.fingerRad,3,1)
        layout.addWidget(fingerGroup)
        
        self.form = form
        self.obj = obj
        
    def accept(self):
        self.obj.Length = self.lSpin.value()
        self.obj.Width = self.wSpin.value()
        self.obj.Depth = self.hSpin.value()
        self.obj.FilletSides = self.sideCheck.isChecked()
        self.obj.SideFilletRadius = self.sideRad.value()
        self.obj.FilletBottom = self.bottomCheck.isChecked()
        self.obj.BottomFilletRadius = self.bottomRad.value()
        self.obj.FingerFront = self.front.isChecked()
        self.obj.FingerBack = self.back.isChecked()
        self.obj.FingerLeft = self.left.isChecked()
        self.obj.FingerRight = self.right.isChecked()
        self.obj.FingerBottom = self.bottom.isChecked()
        self.obj.FingerRadius = self.fingerRad.value()
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self):
        return True

class ViewProviderCompartment:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj, mode):
        return None

    def unsetEdit(self, vobj, mode):
        if mode == 0:
            FreeCADGui.Control.closeDialog()
            return True
        return False

    def setupContextMenu(self, vobj, menu):
        """Add custom context menu entries."""
        action = menu.addAction("Edit Compartment…")
        action.triggered.connect(lambda: FreeCADGui.Control.showDialog(CompartmentTaskPanel(vobj.Object)))

class AddCompartment:
    def GetResources(self):
        return {'MenuText': 'Add Compartment','ToolTip': 'Add a parametric compartment','Pixmap': ''}

    def Activated(self):
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument()
        sel = FreeCADGui.Selection.getSelection()
        if not sel or not hasattr(sel[0].Proxy,"__class__") or sel[0].Proxy.__class__.__name__!="BoxFeature":
            FreeCAD.Console.PrintError("Select a Box to add a compartment.\n"); return
        parent = sel[0]
        obj = doc.addObject("Part::FeaturePython","Compartment")
        CompartmentFeature(obj)
        obj.ViewObject.Proxy = ViewProviderCompartment(obj.ViewObject)
        obj.Placement = parent.Placement
        obj.Placement.Base.x += 2
        obj.Placement.Base.y += 2
        obj.Visibility = False
        # Link compartment to parent
        parent.Compartments = [*parent.Compartments,obj]
        obj.ZOffset = parent.Height - parent.LidThickness if parent.Lid else 0
        doc.recompute()
        FreeCADGui.Control.showDialog(CompartmentTaskPanel(obj))
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        return True

FreeCADGui.addCommand("Add_Compartment_Command", AddCompartment())

