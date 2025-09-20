import FreeCAD, FreeCADGui
import Part
import math


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
    edges_to_fillet = []
    if edge_type == "sides":
        for edge in box.Edges:
            if not math.isclose(edge.Vertexes[0].Point.z, edge.Vertexes[1].Point.z):
                edges_to_fillet.append(edge)
    elif edge_type == "bottom":
        z_min = box.BoundBox.ZMin
        for edge in box.Edges:
            if math.isclose(edge.Vertexes[0].Point.z, z_min) and math.isclose(edge.Vertexes[1].Point.z, z_min):
                edges_to_fillet.append(edge)
    elif edge_type == "top":
        z_max = box.BoundBox.ZMax
        for edge in box.Edges:
            if math.isclose(edge.Vertexes[0].Point.z, z_max) and math.isclose(edge.Vertexes[1].Point.z, z_max):
                edges_to_fillet.append(edge)
    
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
    edges_to_chamfer = []
    for edge in box.Edges:
            if math.isclose(edge.Vertexes[0].Point.z, 0.0) and math.isclose(edge.Vertexes[1].Point.z, 0.0):
                edges_to_chamfer.append(edge)
    try:
        # For a 30-degree chamfer, d2 = d1 / tan(30)
        chamfer_d2 = size / math.tan(math.radians(30))
        chamfered_box = box.makeChamfer(chamfer_d2, size, edges_to_chamfer)
        return chamfered_box
    except Exception as e:
        FreeCAD.Console.PrintError("Failed to create chamfer. Size may be too large or there was another error.")
        FreeCAD.Console.PrintError(str(e))
        return box
