import FreeCAD, FreeCADGui

class ArrangeX:
    def GetResources(self):
        return {'MenuText': 'Arrange X','ToolTip': 'Evenly separate and center compartments','Pixmap': ''}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) < 1:
            return
        compartments = False
        face = None
        for s in sel:
            err = None
            if not s or not hasattr(s.Proxy,"__class__"):
                err = True
            else:
                if s.Proxy.__class__.__name__ == "CompartmentFeature":
                    if face != None:
                        err = True
                    compartments = True
                if s.Proxy.__class__.__name__ == "LabelFeature":
                    if compartments or (face != None and s.Face != face):
                        err = True
                    face = s.Face
            if err:
                FreeCAD.Console.PrintError("Select only compartments or only labels from a single face.\n"); return
        parent = sel[0].InList[1] # get the box or lid parent (not insert)

        # now we know we have consistent objects selected
        xtotal = 0
        for obj in sel:
            if hasattr(obj,"Length"):
                # box compartment
                xtotal += obj.Length.Value
            elif hasattr(obj,"Face"):
                # label
                xtotal += obj.Shape.BoundBox.XLength
            else:
                # polgon or cylinder compartment
                xtotal += obj.Radius.Value * 2
        xgap = (parent.Length.Value - xtotal) / (len(sel) + 1)
        if xgap < 0:
            xgap = 1
            xpos = (parent.Length.Value - (xtotal + xgap * (len(sel) - 1))) / 2
        else:
            xpos = xgap
        sortsel = sorted(sel, key=lambda o: o.Placement.Base.x)
        for obj in sortsel:
            obj.Placement.Base.x = xpos
            xpos += xgap + (obj.Length.Value if hasattr(obj,"Length") else (obj.Shape.BoundBox.XLength if hasattr(obj,"Face") else obj.Radius.Value * 2))

        doc.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        return True

class ArrangeY:
    def GetResources(self):
        return {'MenuText': 'Arrange Y','ToolTip': 'Evenly separate and center compartments','Pixmap': ''}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) < 1:
            return
        compartments = False
        face = None
        for s in sel:
            err = None
            if not s or not hasattr(s.Proxy,"__class__"):
                err = True
            else:
                if s.Proxy.__class__.__name__ == "CompartmentFeature":
                    if face != None:
                        err = True
                    compartments = True
                if s.Proxy.__class__.__name__ == "LabelFeature":
                    if compartments or (face != None and s.Face != face):
                        err = True
                    face = s.Face
            if err:
                FreeCAD.Console.PrintError("Select only compartments or only labels from a single face.\n"); return
        parent = sel[0].InList[1] # get the box or lid parent (not insert)

        # now we know we have consistent objects selected
        ytotal = 0
        for obj in sel:
            if hasattr(obj,"Width"):
                # box compartment
                ytotal += obj.Width.Value
            elif hasattr(obj,"Face"):
                # label
                ytotal += obj.Shape.BoundBox.YLength
            else:
                # polgon or cylinder compartment
                ytotal += obj.Radius.Value * 2
        ygap = (parent.Width.Value - ytotal) / (len(sel) + 1)
        if ygap < 0.5:
            ygap = 1
            ypos = (parent.Width.Value -(ytotal + ygap * (len(sel) - 1))) / 2
        else:
            ypos = ygap
        sortsel = sorted(sel, key=lambda o: o.Placement.Base.y)
        for obj in sortsel:
            obj.Placement.Base.y = ypos
            ypos += ygap + (obj.Width.Value if hasattr(obj,"Width") else (obj.Shape.BoundBox.YLength if hasattr(obj,"Face") else obj.Radius.Value * 2))

        doc.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        return True

class AlignX:
    def GetResources(self):
        return {'MenuText': 'Align X','ToolTip': 'Center compartments or labels along the center of the first selected','Pixmap': ''}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) < 1:
            return
        compartments = False
        face = None
        for s in sel:
            err = None
            if not s or not hasattr(s.Proxy,"__class__"):
                err = True
            else:
                if s.Proxy.__class__.__name__ == "CompartmentFeature":
                    if face != None:
                        err = True
                    compartments = True
                if s.Proxy.__class__.__name__ == "LabelFeature":
                    if compartments or (face != None and s.Face != face):
                        err = True
                    face = s.Face
            if err:
                FreeCAD.Console.PrintError("Select only compartments or only labels from a single face.\n"); return
        parent = sel[0].InList[1] # get the box or lid parent (not insert)

        # now we know we have consistent objects selected
        xcenter = sel[0].Placement.Base.x + (sel[0].Length.Value if hasattr(sel[0],"Length") else (sel[0].Shape.BoundBox.XLength if hasattr(sel[0],"Face") else sel[0].Radius.Value * 2)) / 2
        for obj in sel[1:]:
            obj.Placement.Base.x = xcenter - (obj.Length.Value if hasattr(obj,"Length") else (obj.Shape.BoundBox.XLength if hasattr(obj,"Face") else obj.Radius.Value * 2)) / 2
        doc.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        return True

class AlignY:
    def GetResources(self):
        return {'MenuText': 'Align Y','ToolTip': 'Center compartments or labels along the center of the first selected','Pixmap': ''}

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) < 1:
            return
        compartments = False
        face = None
        for s in sel:
            err = None
            if not s or not hasattr(s.Proxy,"__class__"):
                err = True
            else:
                if s.Proxy.__class__.__name__ == "CompartmentFeature":
                    if face != None:
                        err = True
                    compartments = True
                if s.Proxy.__class__.__name__ == "LabelFeature":
                    if compartments or (face != None and s.Face != face):
                        err = True
                    face = s.Face
            if err:
                FreeCAD.Console.PrintError("Select only compartments or only labels from a single face.\n"); return

        # now we know we have consistent objects selected
        ycenter = sel[0].Placement.Base.y + (sel[0].Width.Value if hasattr(sel[0],"Width") else (sel[0].Shape.BoundBox.YLength if hasattr(sel[0],"Face") else sel[0].Radius.Value * 2)) / 2
        for obj in sel[1:]:
            obj.Placement.Base.y = ycenter - (obj.Width.Value if hasattr(obj,"Width") else (obj.Shape.BoundBox.YLength if hasattr(obj,"Face") else obj.Radius.Value * 2)) / 2
        doc.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")

    def IsActive(self):
        return True
FreeCADGui.addCommand("Arrange_X_Command", ArrangeX())
FreeCADGui.addCommand("Arrange_Y_Command", ArrangeY())
FreeCADGui.addCommand("Align_X_Command", AlignX())
FreeCADGui.addCommand("Align_Y_Command", AlignY())
