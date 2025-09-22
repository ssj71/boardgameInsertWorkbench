import FreeCAD, FreeCADGui
import Part
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
