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

def get_face(parent, face_type):
    """
    Returns the bottom-left and top-right corner points of the specified face of a bounding box.
    Args:
        boundingbox (Part.BoundBox): The bounding box of the object.
        face_type (str): The type of face ("Top", "Front", "Back", "Left", "Right").
    """
    if hasattr(parent, "Height"):
        h = parent.Height.Value
    elif hasattr(parent, "Thickness"):
        h = parent.Thickness.Value
    w = parent.Width.Value
    l = parent.Length.Value
    if face_type == "Front":
        p1 = FreeCAD.Vector(0, 0, 0)
        p2 = FreeCAD.Vector(l, 0, h)
    elif face_type == "Back":
        p1 = FreeCAD.Vector(l, w, 0)
        p2 = FreeCAD.Vector(0, w, h)
    elif face_type == "Left":
        p1 = FreeCAD.Vector(0, w, 0)
        p2 = FreeCAD.Vector(0, 0, h)
    elif face_type == "Right":
        p1 = FreeCAD.Vector(l, 0, 0)
        p2 = FreeCAD.Vector(l, w, h)
    else:  # Top
        p1 = FreeCAD.Vector(0, 0, h)
        p2 = FreeCAD.Vector(l, w, h)
    return p1, p2

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
            # left side
            return FreeCAD.Vector(-1,0,0)
        #right side
        return FreeCAD.Vector(1,0,0)
    elif math.isclose(bottomleft.y, topright.y):
        # XZ plane
        if bottomleft.x > topright.x:
            # back side
            return FreeCAD.Vector(0,1,0)
        #front side
        return FreeCAD.Vector(0,-1,0)
    elif math.isclose(bottomleft.z, topright.z):
        # XY plane
        if bottomleft.x > topright.x:
            # bottom side
            return FreeCAD.Vector(0,0,-1)
        #top side
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
                       bottomleft.x - topright.x,
                       topright.x - bottomleft.x)*normal
    h = FreeCAD.Vector(topright.z - bottomleft.z,
                       topright.z - bottomleft.z,
                       topright.y - bottomleft.y)*normal
    return l,abs(h)

def center_on_face(bottomleft, topright, shape, depth):
    """
    Centers a shape on a specified face defined by two corner points.

    Returns:
        FreeCAD.Vector: The translation vector to center the shape on the face.
    """
    bl = bottomleft
    tr = topright
    bb = shape.BoundBox
    normal = find_plane(bl, tr)
    if hasattr(depth, "Value"):
        depth = depth.Value
    xl = bb.XLength
    yl = bb.YLength
    zl = bb.ZLength
    if normal.dot(FreeCAD.Vector(1,1,1)) < 0:
        normal = -normal
    m2 = FreeCAD.Matrix(FreeCAD.Vector(
                                       bl.x - bb.XMin - depth,
                                       bl.y - bb.YMin + (tr.y - bl.y - yl)/2,
                                       bl.z - bb.ZMin + (tr.z - bl.z - zl)/2),
                        FreeCAD.Vector(
                                       bl.x - bb.XMin + (tr.x - bl.x - xl)/2,
                                       bl.y - bb.YMin - depth,
                                       bl.z - bb.ZMin + (tr.z - bl.z - zl)/2),
                        FreeCAD.Vector(
                                       bl.x - bb.XMin + (tr.x - bl.x - xl)/2,
                                       bl.y - bb.YMin + (tr.y - bl.y - yl)/2,
                                       bl.z - bb.ZMin - depth),
                        FreeCAD.Vector(0,0,0))
    return m2*normal

def zero_shape(shape):
    """
    moves a shape to the origin based on its bounding box

    Args:
        shape (Part.Shape): The shape to be moved
    """
    shape.translate(FreeCAD.Vector(-shape.BoundBox.XMin,
                                   -shape.BoundBox.YMin,
                                   -shape.BoundBox.ZMin))
    return shape

def face_rotation(normal):
    """
    get rotation angle and vector for rotating a shape lying on the XY plane
    (typically an extrusion) to be orthogonal to the given normal vector

    Args:
        normal (FreeCAD.Vector): orthogonal vector to the face of desired orientation

    Returns:
        angle, rotation_vector - the scalar angle in degrees and the rotation axis
        vector to pass into shape.rotate()
    """
    #L -X, 240, -.58, .58, .58
    #R +X, 120, .58, .58, .58
    #F -Y, 90, 1, 0, 0
    #B +Y, 180, 0, -.71, -.71
    #T +Z, 0, 0, 0, 0
    s3 = 3**-0.5 #1/sqrt(3)
    s2 = 2**-0.5 #1/sqrt(2)
    if normal.dot(FreeCAD.Vector(1,1,1)) < 0:
        #front, left, or bottom
        m = FreeCAD.Matrix(FreeCAD.Vector(s3,-s3,-s3), #each vector is a column
                           FreeCAD.Vector(-1,0,0),
                           FreeCAD.Vector(0,0,0),
                           FreeCAD.Vector(0,0,0))
        a = FreeCAD.Vector(-240,-90,0)
    else:
        #back, right, or top
        m = FreeCAD.Matrix(FreeCAD.Vector(s3,s3,s3),
                           FreeCAD.Vector(0,-s2,-s2),
                           FreeCAD.Vector(0,0,0),
                           FreeCAD.Vector(0,0,0))
        a = FreeCAD.Vector(120,180,0)
    rot = m*normal
    angl = a.dot(normal)
    return angl, rot

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

def set_on_face(bottomleft, topright, shape, offset):
    """
    takes an extrusion and places it on the specified face of a box
    
    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner of the label area.
        topright (FreeCAD.Vector): The top-right corner of the label area.
        shape (Part.Shape): The shape to be placed.
        offset (float): The offset distance from the face. if 0 the shape is left at the origin
    """
    normal = find_plane(bottomleft, topright)
    l,h = getlh(bottomleft, topright)
    xl = shape.BoundBox.XLength
    yl = shape.BoundBox.YLength
    if hasattr(offset, "Value"):
        offset = offset.Value
    #first rotate to match the aspect ratio
    if (h > l and xl > yl) or (l > h and yl > xl):
        shape = shape.copy()
        shape.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 90)
        xl,yl = yl,xl
    angl, rot = face_rotation(normal)
    if rot.Length > 0:
        shape = shape.copy()
        shape.rotate(FreeCAD.Vector(0,0,0), rot, angl)
    #now move to the origin
    shape = zero_shape(shape.copy())
    
    if offset == 0:
        return shape.copy()
    #now move centered on the face, with the specified offset
    shape.translate(center_on_face(bottomleft, topright, shape, offset))
    return shape

import Part

def make_faces_from_wires(wires):
    """Build faces correctly from ShapeString wires, preserving holes."""
    faces = []

    # Step 1: Sort by area descending so outers come before inners
    wires = [w for w in wires if w.isClosed()]
    wires.sort(key=lambda w: w.BoundBox.XLength * w.BoundBox.YLength, reverse=True)

    used = set()
    for i, outer in enumerate(wires):
        if i in used:
            continue

        inners = []
        outer_bb = outer.BoundBox
        for j, inner in enumerate(wires):
            if j == i or j in used:
                continue
            # Check if inner wire lies fully inside outer
            if outer_bb.isInside(inner.BoundBox):
                inners.append(inner)
                used.add(j)

        # Create a face from outer + inner wires
        face = Part.Face([outer] + inners)
        faces.append(face)
        used.add(i)

    return faces

def orient_and_extrude(bottomleft, topright, faces, extrudelen):
    """
    Orients and extrudes a shape to fit on a specified face of a box.
    Args:
        bottomleft (FreeCAD.Vector): The bottom-left corner of the label area.
        topright (FreeCAD.Vector): The top-right corner of the label area.
        faces (Part.Shape): The shape to be extruded.
        extrudelen (float): The extrusion length.
    Returns:
        Part.Shape: The extruded shape.
    """
    l,h = getlh(bottomleft, topright)
    normal = find_plane(bottomleft, topright)
    angle, axis = face_rotation(normal)
    if normal.dot(FreeCAD.Vector(1,1,1)) < 0:
        normal = -normal #flip normal if negative so extrusion is always positive
    try:
        if angle != 0:
            faces.rotate(FreeCAD.Vector(0,0,0), axis, angle)
        zero_shape(faces)
        extrusion = faces.extrude(normal*extrudelen.Value)
        return extrusion
    except Exception as e:
        FreeCAD.Console.PrintError(f"Label engraving failed: {e}\n")

def flatten_wire(wire):
    """
    remove any variance in the z direction that can occur from importing SVGs
    Args:
        wire (Part.Wire): The wire to be flattened.
    Returns:
        Part.Wire: The flattened wire.
    """
    # Build a projection matrix that removes the Z component of any point
    m = FreeCAD.Matrix()

    # X' = X*(1,0,0)
    m.A11 = 1; m.A12 = 0; m.A13 = 0; m.A14 = 0
    # Y' = Y*(0,1,0)
    m.A21 = 0; m.A22 = 1; m.A23 = 0; m.A24 = 0
    # Z' = 0*(X,Y,Z) + 0
    m.A31 = 0; m.A32 = 0; m.A33 = 0; m.A34 = 0
    # Homogeneous row
    m.A41 = 0; m.A42 = 0; m.A43 = 0; m.A44 = 1

    # Apply to entire Wire shape (preserves curves)
    return wire.transformGeometry(m)

def svg_label(bottomleft, topright, file, extrudelen, scale=1.0):
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
            wires = [flatten_wire(s.Wires[0]) for s in svgshapes]
            faces = make_faces_from_wires(wires)
            scaledfaces = []
            scale_matrix = FreeCAD.Matrix()
            scale_matrix.scale(scale, scale, scale)
            for face in faces:
                scaledfaces.append(face.transformGeometry(scale_matrix))
            if len(scaledfaces)==0:
                FreeCAD.Console.PrintError("no valid shapes found in the SVG label\n")
                return None
            svg_extrude = orient_and_extrude(bottomleft, topright, Part.Compound(scaledfaces), extrudelen)
            return svg_extrude
    except Exception as e:
        FreeCAD.Console.PrintError(f"An error occurred while processing the SVG label: {str(e)}\n")
    return None

def text_label(bottomleft, topright, string, font, extrudelen, scale=1.0):
    """
    Creates a 3D text label oriented and sized to fit within the specified face of a box.

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
    size = size * scale
    try:
        shapestring = Draft.make_shapestring(string, font, size)
        faces = make_faces_from_wires(shapestring.Shape.Wires)
        cmp = Part.Compound(faces)
        txt_extrude = orient_and_extrude(bottomleft, topright, cmp, extrudelen)
        FreeCAD.ActiveDocument.removeObject(shapestring.Name)
        return txt_extrude
    except Exception as e:
        FreeCAD.Console.PrintError(f"Label engraving failed: {e}\n")

def default_font():
    import os
    workbench_dir = os.path.dirname(__file__)
    return os.path.join(workbench_dir, "libra-serif-modern.regular.otf")
