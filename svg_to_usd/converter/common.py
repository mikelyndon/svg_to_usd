from pxr import Usd, UsdGeom, Sdf

import logging

from . import utils
from .geometry import rect, circle, ellipse, path, line, text, group, polygon, polyline
from . import conversion_options

# TODO: Handle this better
parent_map = {}


def handle_element(usd_stage, svg_element, parent_prim=None):
    global parent_map

    if "clipPath" in parent_map[svg_element].tag:
        return

    _visible = True

    if "fill" in svg_element.attrib:
        if svg_element.attrib['fill'] == "none":
            _visible = False
    if "opacity" in svg_element.attrib:
        if svg_element.attrib['opacity'] == "0":
            _visible = False
    if "style" in svg_element.attrib:
        if "opacity: 0" in svg_element.attrib['style']:
            _visible = False
        if "fill: none" in svg_element.attrib['style']:
            _visible = False
        if "display: none" in svg_element.attrib['style']:
            _visible = False

    svg_id = utils.get_id(svg_element)

    prim_path = "{}".format(svg_id)

    if parent_prim:
        prim_path = parent_prim.GetPath().AppendPath(prim_path)
    else:
        prim_path = Sdf.Path("/" + prim_path)

    usd_mesh = None

    if "rect" in svg_element.tag and conversion_options['convert_rect']:
        usd_mesh = rect.convert(usd_stage, prim_path, svg_element)
    if "ellipse" in svg_element.tag and conversion_options['convert_ellipse']:
        usd_mesh = ellipse.convert(usd_stage, prim_path, svg_element)
    if "circle" in svg_element.tag and conversion_options['convert_circle']:
        usd_mesh = circle.convert(usd_stage, prim_path, svg_element)
    if "path" in svg_element.tag and conversion_options['convert_path']:
        usd_mesh = path.convert(usd_stage, prim_path, svg_element)
    if "polygon" in svg_element.tag and conversion_options['convert_polygon']:
        usd_mesh = polygon.convert(usd_stage, prim_path, svg_element)
    if "polyline" in svg_element.tag and conversion_options['convert_polyline']:
        usd_mesh = polyline.convert(usd_stage, prim_path, svg_element)
    if svg_element.tag.rpartition('}')[-1] == "line" and conversion_options['convert_line']:
        usd_mesh = line.convert(usd_stage, prim_path, svg_element)
    if "text" in svg_element.tag and conversion_options['convert_text']:
        usd_mesh = text.convert(usd_stage, prim_path, svg_element,
                                fallback_font=conversion_options['fallback_font'])
    if svg_element.tag.rpartition('}')[-1] == "g" and conversion_options['convert_group']:
        usd_mesh = group.convert(usd_stage, prim_path, svg_element)

    if not usd_mesh:
        # Something has failed in generation, or unsupported svg element
        logging.debug(f"SVG tag '{svg_element.tag}' unsupported")
        return

    # TODO: Handle visibility properly
    if 'visibility' in svg_element.attrib:
        if svg_element.attrib['visibility'] == "hidden":
            _visible = False

    # Author visibility
    if not _visible:
        if 'force_visibility' in conversion_options and conversion_options['force_visibility'] == True:
            pass
        else:
            usd_mesh.CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible)

    return usd_mesh


def handle_svg_root(stage, root, parent_prim=None):
    for elem in root:
        usd_prim = handle_element(stage, elem, parent_prim)
        handle_svg_root(stage, elem, usd_prim)
