import FreeCAD, FreeCADGui
from PySide import QtGui
import Draft, importSVG, Part, math, os
import common

class LabelFeature:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyBool", "LidLabel", "Label", "Label is for lid").LidLabel = False
        obj.addProperty("App::PropertyEnumeration", "Face", "Label",
                        "Box face label will be placed on").Face = ["Front", "Back", "Left", "Right", ""]
        
        obj.addProperty("App::PropertyLength", "Depth", "Label", "Engraving Depth").Depth = 1.0
        obj.addProperty("App::PropertyString", "LabelText", "Label", "Text label for this compartment").LabelText = "Label"
        workbench_dir = os.path.dirname(__file__)
        obj.addProperty("App::PropertyFile", "FontFile", "Label", "Path to TTF/OTF font file").FontFile = common.default_font()
        obj.addProperty("App::PropertyFile", "SVGFile", "Label", "Path to SVG font file").SVGFile = ""
        obj.addProperty("App::PropertyFloat", "Scale", "Label", "Additional Scaling Factor").Scale = 1.0

    def execute(self, obj):
        for p in obj.InList:
            if p.Proxy.__class__.__name__ in ["BoxFeature","LidFeature"]:
                parent = p
                break
        if not parent or not hasattr(parent, "Shape") or parent.Shape.isNull():
            obj.Shape = Part.Shape()
            return
        if obj.LidLabel:
            p1, p2 = common.get_face(parent, "Top")
        else:
            p1, p2 = common.get_face(parent, obj.Face)
        label = None
        if obj.SVGFile:
            label = common.svg_label(p1, p2, obj.SVGFile, 2*obj.Depth, obj.Scale)
        elif obj.LabelText and obj.FontFile:
            label = common.text_label(p1, p2, obj.LabelText, obj.FontFile, 2*obj.Depth, obj.Scale)
        if not label or label.isNull():
            obj.Shape = Part.Shape()
            return
        obj.Shape = label

class ViewProviderLabel:
    def __init__(self, vobj):
        vobj.Proxy = self

    def setEdit(self, vobj, mode):
        return None

    def unsetEdit(self, vobj, mode):
        if mode == 0:
            FreeCADGui.Control.closeDialog()
            return True
        return False

def create_label(parent):
    doc = FreeCAD.ActiveDocument
    obj = doc.addObject("Part::FeaturePython","Label")
    LabelFeature(obj)
    if parent.Proxy.__class__.__name__=="LidFeature":
        obj.LidLabel = True
    #add it to the insert as a sibling to the box
    parent.InList[0].addObject(obj)
    obj.ViewObject.Proxy = ViewProviderLabel(obj.ViewObject)
    obj.Visibility = False
    # Link compartment to parent
    parent.Labels = [*parent.Labels, obj]
    return obj


# ---------------- TaskPanel ----------------
class LabelTaskPanel:
    def __init__(self, obj):
        self.obj = obj
        self.form = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.form)

        #this task can create multiple labels
        if not obj[0].LidLabel:
            # Face selection
            fGroup = QtGui.QGroupBox("Label Locations")
            fl = QtGui.QHBoxLayout(fGroup)
            self.chkFront = QtGui.QCheckBox("Front");  self.chkFront.setChecked(obj[0].Face=="Front")
            self.chkBack  = QtGui.QCheckBox("Back");   self.chkBack.setChecked(obj[0].Face=="Back")
            self.chkLeft  = QtGui.QCheckBox("Left");   self.chkLeft.setChecked(obj[0].Face=="Left")
            self.chkRight = QtGui.QCheckBox("Right");  self.chkRight.setChecked(obj[0].Face=="Right")
            fl.addWidget(self.chkFront)
            fl.addWidget(self.chkBack)
            fl.addWidget(self.chkLeft)
            fl.addWidget(self.chkRight)
            self.layout.addWidget(fGroup)

        # Depth spin
        fl = QtGui.QFormLayout()
        self.depthSpin = QtGui.QDoubleSpinBox()
        self.depthSpin.setRange(0, 100)
        self.depthSpin.setValue(obj[0].Depth)
        fl.addRow("Depth:", self.depthSpin)
        self.layout.addLayout(fl)

        # label group
        lGroup = QtGui.QGroupBox("Label")
        fl = QtGui.QFormLayout(lGroup)
        self.labelEdit = QtGui.QLineEdit(self.obj[0].LabelText)
        self.fontEdit = QtGui.QLineEdit(self.obj[0].FontFile)
        self.fontButton = QtGui.QPushButton("Browse...")
        fontLayout = QtGui.QHBoxLayout()
        fontLayout.addWidget(self.fontEdit)
        fontLayout.addWidget(self.fontButton)
        self.svgEdit = QtGui.QLineEdit(self.obj[0].SVGFile)
        self.svgButton = QtGui.QPushButton("Browse...")
        svgLayout = QtGui.QHBoxLayout()
        svgLayout.addWidget(self.svgEdit)
        svgLayout.addWidget(self.svgButton)
        self.scaleSpin = QtGui.QDoubleSpinBox()
        self.scaleSpin.setRange(0, 800)
        self.scaleSpin.setValue(obj[0].Scale)
        fl.addRow("Text:", self.labelEdit)
        fl.addRow("Font:", fontLayout)
        fl.addRow("SVG:", svgLayout)
        fl.addRow("Scale %:", self.scaleSpin)
        self.fontButton.clicked.connect(self.chooseFont)
        self.svgButton.clicked.connect(self.chooseSVG)
        self.layout.addWidget(lGroup)

    def chooseFont(self):
        fn, _ = QtGui.QFileDialog.getOpenFileName(None, "Select Font", "", "Fonts (*.ttf *.otf)")
        if fn:
            self.fontEdit.setText(fn)
    def chooseSVG(self):
        fn, _ = QtGui.QFileDialog.getOpenFileName(None, "Select SVG Image", "", "svg files (*.svg)")
        if fn:
            self.svgEdit.setText(fn)

    def accept(self):
        parent = self.obj[0].InList[1] #first parent is the insert
        if not self.obj[0].LidLabel:
            sides = []
            if self.chkFront.isChecked():
                sides.append("Front")
            if self.chkBack.isChecked():
                sides.append("Back")
            if self.chkLeft.isChecked():
                sides.append("Left")
            if self.chkRight.isChecked():
                sides.append("Right")
            if len(sides) > len(self.obj):
                for i in range(len(self.obj), len(sides)):
                    self.obj.append(create_label(parent))
            elif len(sides) < len(self.obj):
                for obj in self.obj[len(sides):]:
                    parent.removeObject(obj)
                    FreeCAD.ActiveDocument.removeObject(obj.Name)
        else:
            sides = [""]
        for i,obj in enumerate(self.obj):
            obj.Depth = self.depthSpin.value()
            obj.Face = sides[i]
            
            # label values
            obj.LabelText  = self.labelEdit.text()
            obj.FontFile   = self.fontEdit.text()
            obj.SVGFile    = self.svgEdit.text()
            obj.Scale      = self.scaleSpin.value()

            # recompute to update shape
            obj.recompute()

            # place on face
            p1, p2 = common.get_face(parent, obj.Face)
            obj.Placement.Base = common.center_on_face(p1, p2, obj.Shape, obj.Depth)

            # name it
            if len(obj.Face) == 0:
                s = "_Lid"
            else:
                s = "_" + obj.Face[0]
            if obj.SVGFile:
                name = os.path.split(obj.SVGFile)[-1].split(".")[0] + s + "_Label"
            else:
                name = obj.LabelText + s + "_Label"
            obj.Label = name
        
        FreeCAD.ActiveDocument.recompute()
        return True

    def reject(self): return True

class AddLabel:
    def GetResources(self):
        return {'MenuText': 'Add Label','ToolTip': 'Add a label to a box or lid','Pixmap': ''}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if not sel or not hasattr(sel[0].Proxy,"__class__") or (sel[0].Proxy.__class__.__name__ not in ["BoxFeature", "InsertFeature", "LidFeature"]):
            FreeCAD.Console.PrintError("Select an insert box or lid to add a label.\n"); return
        if sel[0].Proxy.__class__.__name__=="InsertFeature":
            # get the box inside the insert
            for obj in sel[0].Group:
                if obj.Proxy.__class__.__name__=="BoxFeature":
                    parent = obj
        else:
            # they selected the box or lid directly
            parent = sel[0]
        obj = create_label(parent)
        doc.recompute()
        FreeCADGui.Control.showDialog(LabelTaskPanel([obj]))
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        return True

FreeCADGui.addCommand("Add_Label_Command", AddLabel())

