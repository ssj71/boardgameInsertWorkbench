import FreeCAD, FreeCADGui
from PySide import QtGui
import Draft, Part, math, common

class CompartmentFeature:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyEnumeration", "ShapeType", "Compartment",
                        "Compartment shape type").ShapeType = ["Box","Cylinder","Polygon","Box2"]
        obj.ShapeType = "Box"
        
        obj.addProperty("App::PropertyLength", "Depth", "Compartment", "Depth").Depth = 30.0
        obj.addProperty("App::PropertyLength", "ZOffset", "Compartment", "Z offset").ZOffset = 0.0
        
        # common to all: finger holes
        obj.addProperty("App::PropertyLength", "FingerRadius", "FingerHoles", "Finger hole radius").FingerRadius = 10.0
        #obj.addProperty("App::PropertyBool", "FingerFront", "FingerHoles", "Front").FingerRadius = 10.0
        for name in ["FingerFront","FingerBack","FingerLeft","FingerRight","FingerBottom"]:
            obj.addProperty("App::PropertyBool", name, "FingerHoles", name)
            setattr(obj,name,False)
        
       # Label options
        obj.addProperty("App::PropertyString", "LabelText", "Label", "Text label for this compartment").LabelText = ""
        obj.addProperty("App::PropertyFile", "FontFile", "Label", "Path to TTF font file").FontFile = ""
        
        self.ensureProperties(obj)

    def ensureProperties(self, obj):
        """Ensure properties match current ShapeType"""
        st = obj.ShapeType
        # remove old shape-specific properties
        for pname in ["Length","Width","Radius","Sides",
                      "SideFilletRadius","BottomFilletRadius"]:
            if pname in obj.PropertiesList:
                obj.removeProperty(pname)
        
        if st == "Box":
            obj.addProperty("App::PropertyLength","Length","Box","Length").Length=91
            obj.addProperty("App::PropertyLength","Width","Box","Width").Width=64.5
            obj.addProperty("App::PropertyLength","SideFilletRadius","Box","Side fillet radius").SideFilletRadius=2
            obj.addProperty("App::PropertyLength","BottomFilletRadius","Box","Bottom fillet radius").BottomFilletRadius=0
        
        elif st == "Box2":
            obj.addProperty("App::PropertyLength","Length","Box2","Length").Length=40
            obj.addProperty("App::PropertyLength","Width","Box2","Width").Width=30
            obj.addProperty("App::PropertyLength","BottomFilletRadius","Box2","Bottom fillet radius").BottomFilletRadius=2
        
        elif st == "Cylinder":
            obj.addProperty("App::PropertyLength","Radius","Cylinder","Radius").Radius=15
            obj.addProperty("App::PropertyLength","BottomFilletRadius","Cylinder","Bottom fillet radius").BottomFilletRadius=0
        
        elif st == "Polygon":
            obj.addProperty("App::PropertyInteger","Sides","Polygon","Number of sides").Sides=6
            obj.addProperty("App::PropertyLength","Radius","Polygon","Radius").Radius=10
            obj.addProperty("App::PropertyLength","SideFilletRadius","Polygon","Side fillet radius").SideFilletRadius=2
            obj.addProperty("App::PropertyLength","BottomFilletRadius","Polygon","Bottom fillet radius").BottomFilletRadius=0

    def onChanged(self, obj, prop):
        if prop=="ShapeType":
            self.ensureProperties(obj)

    def execute(self, obj):
        z = obj.ZOffset - obj.Depth
        st = obj.ShapeType
        
        if st == "Box":
            shape = Part.makeBox(obj.Length,obj.Width,2*obj.Depth,FreeCAD.Vector(0,0,z))
            if obj.SideFilletRadius:
                shape = common.fillet_edges(shape,obj.SideFilletRadius,"sides")
            if obj.BottomFilletRadius:
                shape = common.fillet_edges(shape,obj.BottomFilletRadius,"bottom")
        elif st == "Box2":
            shape = Part.makeBox(obj.Length,obj.Width,2*obj.Depth,FreeCAD.Vector(0,0,z))
            if obj.BottomFilletRadius:
                shape = common.fillet_edges(shape,obj.BottomFilletRadius,"bottom2")
        
        elif st == "Cylinder":
            shape = Part.makeCylinder(obj.Radius,2*obj.Depth,FreeCAD.Vector(obj.Radius,obj.Radius,z))
            if obj.BottomFilletRadius:
                shape = common.fillet_edges(shape,obj.BottomFilletRadius,"bottom")
        
        elif st == "Polygon":
            poly = Part.makePolygon([FreeCAD.Vector(
                math.cos(2*math.pi*i/obj.Sides)*obj.Radius,
                math.sin(2*math.pi*i/obj.Sides)*obj.Radius,0)
                for i in range(obj.Sides+1)])
            face = Part.Face(poly)
            shape = face.extrude(FreeCAD.Vector(0,0,2*obj.Depth))
            shape.translate(FreeCAD.Vector(obj.Radius,obj.Radius,z))
            if obj.SideFilletRadius:
                shape = common.fillet_edges(shape,obj.SideFilletRadius,"sides")
            if obj.BottomFilletRadius:
                shape = common.fillet_edges(shape,obj.BottomFilletRadius,"bottom")
        
        # --- add finger holes ---
        shapes = [shape]
        r = obj.FingerRadius
        h = obj.Depth * 2
        one = FreeCAD.Units.Quantity("1 mm")
        cx = shape.BoundBox.XLength/2
        cy = shape.BoundBox.YLength/2
        if obj.FingerFront: shapes.append(Part.makeCylinder(r,h,FreeCAD.Vector(cx,0,z-one)))
        if obj.FingerBack:  shapes.append(Part.makeCylinder(r,h,FreeCAD.Vector(cx,shape.BoundBox.YMax,z-one)))
        if obj.FingerLeft:  shapes.append(Part.makeCylinder(r,h,FreeCAD.Vector(0,cy,z-one)))
        if obj.FingerRight: shapes.append(Part.makeCylinder(r,h,FreeCAD.Vector(shape.BoundBox.XMax,cy,z-one)))
        if obj.FingerBottom:shapes.append(Part.makeCylinder(r,h,FreeCAD.Vector(cx,cy,-one)))
        
        # ----- add label engraving -----
        if obj.LabelText and obj.FontFile:
            #size the label
            bb = shape.BoundBox
            if bb.XLength > bb.YLength:
                size = bb.XLength / (len(obj.LabelText) * 1.3)
            else:
                size = bb.YLength / (len(obj.LabelText) * 1.3)
            if size > bb.XLength: size = bb.XLength * .9
            if size > bb.YLength: size = bb.YLength * .9
            try:
                shapestring = Draft.make_shapestring(obj.LabelText, obj.FontFile, size)
                faces = [Part.Face(wire) for wire in shapestring.Shape.Wires if wire.isClosed()]
                txt_extrude = Part.Compound(faces).extrude(FreeCAD.Vector(0,0,obj.Depth))
                xl = txt_extrude.BoundBox.XLength
                yl = txt_extrude.BoundBox.YLength
                if bb.YLength > bb.XLength:
                    txt_extrude.rotate(FreeCAD.Vector(xl/2,yl/2,0), FreeCAD.Vector(0,0,1), 90)
                txt_extrude.translate(FreeCAD.Vector(
                    bb.XMin + (bb.XLength - xl)/2,
                    bb.YMin + (bb.YLength - yl)/2,
                    obj.ZOffset - obj.Depth - one/2))  # just below bottom
                FreeCAD.ActiveDocument.removeObject(shapestring.Name)
                shapes.append(txt_extrude)
            except Exception as e:
                FreeCAD.Console.PrintError(f"Label engraving failed: {e}\n")

        obj.Shape = Part.makeCompound(shapes)

# ---------------- TaskPanel ----------------
class CompartmentTaskPanel:
    def __init__(self, obj):
        self.obj = obj
        self.form = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.form)

        # shape selector
        self.typeCombo = QtGui.QComboBox()
        self.typeCombo.addItems(["Box","Cylinder","Polygon","Box2"])
        self.typeCombo.setCurrentText(obj.ShapeType)
        self.layout.addWidget(self.typeCombo)

        # dynamic shape-specific area
        self.dynamicArea = QtGui.QVBoxLayout()
        self.layout.addLayout(self.dynamicArea)

        # common finger hole group
        fGroup = QtGui.QGroupBox("Finger Holes")
        fl = QtGui.QFormLayout(fGroup)
        self.rSpin = QtGui.QDoubleSpinBox(); self.rSpin.setRange(0,1000); self.rSpin.setValue(obj.FingerRadius)
        self.chkFront = QtGui.QCheckBox("Front");  self.chkFront.setChecked(obj.FingerFront)
        self.chkBack  = QtGui.QCheckBox("Back");   self.chkBack.setChecked(obj.FingerBack)
        self.chkLeft  = QtGui.QCheckBox("Left");   self.chkLeft.setChecked(obj.FingerLeft)
        self.chkRight = QtGui.QCheckBox("Right");  self.chkRight.setChecked(obj.FingerRight)
        self.chkBottom= QtGui.QCheckBox("Bottom"); self.chkBottom.setChecked(obj.FingerBottom)
        fl.addRow("Radius:", self.rSpin)
        fl.addRow(self.chkFront, self.chkBack)
        fl.addRow(self.chkLeft, self.chkRight)
        fl.addRow(self.chkBottom)
        self.layout.addWidget(fGroup)

        # label group
        lGroup = QtGui.QGroupBox("Label")
        fl = QtGui.QFormLayout(lGroup)
        self.labelEdit = QtGui.QLineEdit(self.obj.LabelText)
        self.fontEdit = QtGui.QLineEdit(self.obj.FontFile)
        self.fontButton = QtGui.QPushButton("Browse...")
        fontLayout = QtGui.QHBoxLayout()
        fontLayout.addWidget(self.fontEdit)
        fontLayout.addWidget(self.fontButton)
        fl.addRow("Text:", self.labelEdit)
        fl.addRow("Font:", fontLayout)
        self.fontButton.clicked.connect(self.chooseFont)
        self.layout.addWidget(lGroup)

        self.typeCombo.currentIndexChanged.connect(self.rebuildForm)
        self.rebuildForm()

    def chooseFont(self):
        fn, _ = QtGui.QFileDialog.getOpenFileName(None, "Select Font", "", "Fonts (*.ttf *.otf)")
        if fn:
            self.fontEdit.setText(fn)

    def clearLayout(self,layout):
        while layout.count():
            item = layout.takeAt(0)
            w=item.widget()
            if w: w.deleteLater()
            elif item.layout(): self.clearLayout(item.layout())

    def rebuildForm(self):
        self.clearLayout(self.dynamicArea)
        st = self.typeCombo.currentText()
        
        if st in ["Box","Box2"]:
            lGroup = QtGui.QGroupBox("Dimensions")
            fl = QtGui.QFormLayout(lGroup)
            self.lSpin = QtGui.QDoubleSpinBox(); self.lSpin.setRange(0,1000); self.lSpin.setValue(getattr(self.obj,"Length",40))
            self.wSpin = QtGui.QDoubleSpinBox(); self.wSpin.setRange(0,1000); self.wSpin.setValue(getattr(self.obj,"Width",30))
            self.depthSpin = QtGui.QDoubleSpinBox(); self.depthSpin.setRange(0,1000); self.depthSpin.setValue(self.obj.Depth)
            fl.addRow("Length:", self.lSpin)
            fl.addRow("Width:", self.wSpin)
            fl.addRow("Depth:", self.depthSpin)
            self.dynamicArea.addWidget(lGroup)
        
        if st=="Cylinder":
            g=QtGui.QGroupBox("Dimensions")
            fl=QtGui.QFormLayout(g)
            self.radSpin=QtGui.QDoubleSpinBox(); self.radSpin.setRange(0,1000); self.radSpin.setValue(getattr(self.obj,"Radius",20))
            self.depthSpin = QtGui.QDoubleSpinBox(); self.depthSpin.setRange(0,1000); self.depthSpin.setValue(self.obj.Depth)
            fl.addRow("Radius:",self.radSpin)
            fl.addRow("Depth:", self.depthSpin)
            self.dynamicArea.addWidget(g)
        
        if st=="Polygon":
            g=QtGui.QGroupBox("Polygon")
            fl=QtGui.QFormLayout(g)
            self.sSpin=QtGui.QSpinBox(); self.sSpin.setRange(3,20); self.sSpin.setValue(getattr(self.obj,"Sides",6))
            self.radSpin=QtGui.QDoubleSpinBox(); self.radSpin.setRange(0,1000); self.radSpin.setValue(getattr(self.obj,"Radius",20))
            self.depthSpin = QtGui.QDoubleSpinBox(); self.depthSpin.setRange(0,1000); self.depthSpin.setValue(self.obj.Depth)
            fl.addRow("Sides:",self.sSpin)
            fl.addRow("Radius:",self.radSpin)
            fl.addRow("Depth:", self.depthSpin)
            self.dynamicArea.addWidget(g)
        
        if st in ["Box","Polygon"]:
            fGroup = QtGui.QGroupBox("Fillets")
            fl = QtGui.QFormLayout(fGroup)
            self.sideSpin = QtGui.QDoubleSpinBox(); self.sideSpin.setRange(0,1000); self.sideSpin.setValue(getattr(self.obj,"SideFilletRadius",0))
            self.bottomSpin = QtGui.QDoubleSpinBox(); self.bottomSpin.setRange(0,1000); self.bottomSpin.setValue(getattr(self.obj,"BottomFilletRadius",0))
            fl.addRow("Side Radius:", self.sideSpin)
            fl.addRow("Bottom Radius:", self.bottomSpin)
            self.dynamicArea.addWidget(fGroup)
        
        if st in ["Box2","Cylinder"]:
            fGroup = QtGui.QGroupBox("Fillets")
            fl = QtGui.QFormLayout(fGroup)
            self.bottomSpin = QtGui.QDoubleSpinBox(); self.bottomSpin.setRange(0,1000); self.bottomSpin.setValue(getattr(self.obj,"BottomFilletRadius",0))
            fl.addRow("Bottom Radius:", self.bottomSpin)
            self.dynamicArea.addWidget(fGroup)

    def accept(self):
        st = self.typeCombo.currentText()
        self.obj.ShapeType = st
        self.obj.Depth = self.depthSpin.value()
        if st in ["Box","Box2"]:
            self.obj.Length = self.lSpin.value()
            self.obj.Width  = self.wSpin.value()
        if st in ["Box","Polygon"]:
            self.obj.SideFilletRadius = self.sideSpin.value()
            self.obj.BottomFilletRadius = self.bottomSpin.value()
        if st in ["Box2","Cylinder"]:
            self.obj.BottomFilletRadius = self.bottomSpin.value()
        if st=="Cylinder":
            self.obj.Radius=self.radSpin.value()
        if st=="Polygon":
            self.obj.Radius=self.radSpin.value()
            self.obj.Sides=self.sSpin.value()
        
        # finger hole values
        self.obj.FingerRadius = self.rSpin.value()
        self.obj.FingerFront  = self.chkFront.isChecked()
        self.obj.FingerBack   = self.chkBack.isChecked()
        self.obj.FingerLeft   = self.chkLeft.isChecked()
        self.obj.FingerRight  = self.chkRight.isChecked()
        self.obj.FingerBottom = self.chkBottom.isChecked()
        
        # label values
        self.obj.LabelText  = self.labelEdit.text()
        self.obj.FontFile   = self.fontEdit.text()
        
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self): return True

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

