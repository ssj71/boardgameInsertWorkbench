import FreeCAD, FreeCADGui
import Part, importSVG, Draft
import math

def get_edges(box, edge_type):
    found_edges = []
    if edge_type == "sides":
        for edge in box.Edges:
            if not math.isclose(edge.Vertexes[0].Point.z, edge.Vertexes[1].Point.z):
                found_edges.append(edge)
    elif edge_type == "bottom" or edge_type == "bottom2":
        z_min = box.BoundBox.ZMin
        for edge in box.Edges:
            if math.isclose(edge.Vertexes[0].Point.z, z_min) and (len(edge.Vertexes) == 1 or math.isclose(edge.Vertexes[1].Point.z, z_min)):
                if edge_type != "bottom2" or edge.Vertexes[0].Point.x == edge.Vertexes[1].Point.x:
                    #all bottom or just those that are parallel to the X axis
                    found_edges.append(edge)
    elif edge_type == "top":
        z_max = box.BoundBox.ZMax
        for edge in box.Edges:
            if math.isclose(edge.Vertexes[0].Point.z, z_max) and math.isclose(edge.Vertexes[1].Point.z, z_max):
                found_edges.append(edge)
    return found_edges

def get_face(boundingbox, face_type):
    """
    Returns the bottom-left and top-right corner points of the specified face of a bounding box.
    Args:
        boundingbox (Part.BoundBox): The bounding box of the object.
        face_type (str): The type of face ("Top", "Front", "Back", "Left", "Right").
    """
    bb = boundingbox
    if face_type == "Front":
        p1 = FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMin)
        p2 = FreeCAD.Vector(bb.XMax, bb.YMin, bb.ZMax)
    elif face_type == "Back":
        p1 = FreeCAD.Vector(bb.XMin, bb.YMax, bb.ZMin)
        p2 = FreeCAD.Vector(bb.XMax, bb.YMax, bb.ZMax)
    elif face_type == "Left":
        p1 = FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMin)
        p2 = FreeCAD.Vector(bb.XMin, bb.YMax, bb.ZMax)
    elif face_type == "Right":
        p1 = FreeCAD.Vector(bb.XMax, bb.YMin, bb.ZMin)
        p2 = FreeCAD.Vector(bb.XMax, bb.YMax, bb.ZMax)
    else:  # Top
        p1 = FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMax)
        p2 = FreeCAD.Vector(bb.XMax, bb.YMax, bb.ZMax)
    return p1, p2

def fillet_edges(box, radius, edge_type):
    """
    Applies a fillet to a list of edges on a given Part.Shape based on a type.
    
    Args:
        box (Part.Shape): The Part.Shape to modify.
        radius (float): The fillet radius.
        edge_type (str): The type of edges to fillet ("sides", "bottom", or "top").
    
    Returns:
        Part.Shape: The new shape after the fillet operation, or the original
                    shape if the operation fails.
    """
    edges_to_fillet = get_edges(box, edge_type)
    if not edges_to_fillet:
        return box
    try:
        filleted_box = box.makeFillet(radius, edges_to_fillet)
        return filleted_box
    except:
        FreeCAD.Console.PrintError(f"Failed to create {edge_type} fillet. Radius may be too large.")
        return box

def chamfer_bottom(box, size):
    """
    Applies a 30-degree chamfer to the bottom of a Part.Shape.
    
    Args:
        box (Part.Shape): The Part.Shape to modify.
        size (float): The horizontal size of the chamfer.
    
    Returns:
        Part.Shape: The new shape after the chamfer operation, or the original
                    shape if the operation fails.
    """
    edges_to_chamfer = get_edges(box, "bottom")
    try:
        # For a 30-degree chamfer, d2 = d1 / tan(30)
        chamfer_d2 = size / math.tan(math.radians(30))
        chamfered_box = box.makeChamfer(chamfer_d2, size, edges_to_chamfer)
        return chamfered_box
    except Exception as e:
        FreeCAD.Console.PrintError("Failed to create chamfer. Size may be too large or there was another error.")
        FreeCAD.Console.PrintError(str(e))
        return box

def find_plane(bottomleft, topright):
    """
    Determines the plane and normal vector based on two corner points.
    
    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner point.
        topright (FreeCAD.Vector): The top-right corner point.
    
    Returns:
        tuple: normal vector (FreeCAD.Vector).
    """
    if math.isclose(bottomleft.x, topright.x):
        # YZ plane
        if bottomleft.y > topright.y:
            # normal points outwards
            return FreeCAD.Vector(-1,0,0)
        return FreeCAD.Vector(1,0,0)
    elif math.isclose(bottomleft.y, topright.y):
        # XZ plane
        if bottomleft.x > topright.x:
            # normal points outwards
            return FreeCAD.Vector(0,-1,0)
        return FreeCAD.Vector(0,1,0)
    elif math.isclose(bottomleft.z, topright.z):
        # XY plane
        if bottomleft.x > topright.x:
            # normal points outwards
            return FreeCAD.Vector(0,0,-1)
        return FreeCAD.Vector(0,0,1)
    else:
        return None, None

def getlh(bottomleft, topright):
    """
    get the length and width of a rectangle based on 2 corners
    the rectangle must be parallel to the cardinal axes.

    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner of the rectangle
        topright (FreeCAD.Vector): The top-right corner of the rectangle
    """
    normal = find_plane(bottomleft, topright)
    l = FreeCAD.Vector(topright.y - bottomleft.y,
                       topright.x - bottomleft.x,
                       topright.x - bottomleft.x)*normal
    h = FreeCAD.Vector(topright.z - bottomleft.z,
                       topright.z - bottomleft.z,
                       topright.y - bottomleft.y)*normal
    return l,h

def set_on_face(bottomleft, topright, shape, offset):
    """
    takes an extrusion and places it on the specified face of a box
    
    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner of the label area.
        topright (FreeCAD.Vector): The top-right corner of the label area.
        shape (Part.Shape): The shape to be placed.
        offset (float): The offset distance from the face.
    """
    normal = find_plane(bottomleft, topright)
    l,h = getlh(bottomleft, topright)
    xl = shape.BoundBox.XLength
    yl = shape.BoundBox.YLength
    print(normal, l,h,xl,yl)
    if hasattr(offset, "Value"):
        offset = offset.Value
    #first rotate to match the aspect ratio
    if h > l and xl > yl or yl > xl:
        shape.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90)
        xl,yl = yl,xl
    #now rotate to the correct face
    m = FreeCAD.Matrix(FreeCAD.Vector(1,1,1), #each vector is a column
                       FreeCAD.Vector(1,0,0),
                       FreeCAD.Vector(0,0,0),
                       FreeCAD.Vector(0,0,0))
    #now move to the origin
    shape.translate(FreeCAD.Vector(-shape.BoundBox.XMin,
                                   -shape.BoundBox.YMin,
                                   -shape.BoundBox.ZMin))
    rot = m*normal
    if rot.Length > 0:
        shape.rotate(FreeCAD.Vector(0,0,0), rot, 75 + 15*rot.Length**2)
    
    #now move centered on the face, with the specified offset
    bl = bottomleft
    tr = topright
    bb = shape.BoundBox
    m2 = FreeCAD.Matrix(FreeCAD.Vector(
                                       bl.x - bb.XMin + offset,
                                       bl.y - bb.YMin + (tr.y - bl.y - xl)/2,
                                       bl.z - bb.ZMin + (tr.z - bl.z - yl)/2),
                        FreeCAD.Vector(
                                       bl.x - bb.XMin + (tr.x - bl.x - xl)/2,
                                       bl.y - bb.YMin + offset,
                                       bl.z - bb.ZMin + (tr.z - bl.z - yl)/2),
                        FreeCAD.Vector(
                                       bl.x - bb.XMin + (tr.x - bl.x - xl)/2,
                                       bl.y - bb.YMin + (tr.y - bl.y - yl)/2,
                                       bl.z - bb.ZMin + offset),
                        FreeCAD.Vector(0,0,0))
    shape.translate(m2*normal)
    return shape

def svg_label(file, extrudelen):
    """
    Creates a 3D label from an SVG file and places it on a specified face of a box.
    
    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner of the label area.
        topright (FreeCAD.Vector): The top-right corner of the label area.
        file (str): The path to the SVG file.
        extrudelen (float): The extrusion length for the label.
    
    Returns:
        Part.Shape: The new shape, or None if the operation fails.
    """
    try:
        svgdoc = importSVG.open(file)
        svgshapes = [s.Shape for s in svgdoc.Objects if hasattr(s,"Shape") and not s.Shape.isNull()]
        FreeCAD.closeDocument(svgdoc.Name)
        if svgshapes:
            faces = [Part.Face(wire) for wire in svgshapes if wire.isClosed()]
            if len(faces)==0:
                print("No closed shapes found in SVG for extrusion.")
                faces = svgshapes
            svg_extrude = Part.Compound(faces).extrude(FreeCAD.Vector(0,0, extrudelen))
            
            return svg_extrude
    except Exception as e:
        FreeCAD.Console.PrintError(f"An error occurred while processing the SVG label: {str(e)}\n")
    return None

def text_label(bottomleft, topright, string, font, extrudelen):
    """
    Creates a 3D text label sized to fit within the specified face of a box.

    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner of the label area.
        topright (FreeCAD.Vector): The top-right corner of the label area.
        string (str): The text string for the label.
        font (str): The font name for the text.
        extrudelen (float): The extrusion length for the text.
    """
    l,h = getlh(bottomleft, topright)
    if l > h:
        size = l / (len(string) * 1.3)
    else:
        size = h / (len(string) * 1.3)
    if size > l: size = l * .9
    if size > h: size = h * .9
    try:
        shapestring = Draft.make_shapestring(string, font, size)
        faces = [Part.Face(wire) for wire in shapestring.Shape.Wires if wire.isClosed()]
        txt_extrude = Part.Compound(faces).extrude(FreeCAD.Vector(0,0,extrudelen))
        xl = txt_extrude.BoundBox.XLength
        yl = txt_extrude.BoundBox.YLength
        FreeCAD.ActiveDocument.removeObject(shapestring.Name)
        return txt_extrude
    except Exception as e:
        FreeCAD.Console.PrintError(f"Label engraving failed: {e}\n")

def default_font():
    import os
    workbench_dir = os.path.dirname(__file__)
    return os.path.join(workbench_dir, "libra-serif-modern.regular.otf")
