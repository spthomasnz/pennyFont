import xml.etree.ElementTree as ET
from shapely.affinity import affine_transform
from typing import Union
from shapely.geometry import MultiPolygon

def poly_to_svg(poly, style=None):

    if type(poly) is MultiPolygon:
        poly_svg = "\n\t".join([poly_to_svg(p, style=style) for p in poly.geoms])

        return f"<g>{poly_svg}</g>"

    if style is None:
        style_str = ""
    else:
        style_str = " ".join([f"{k}:{v};" for k, v in style.items()])

    raw_svg = poly.svg()
    svg_xml = ET.fromstring(raw_svg)

    try:
        d_attr = svg_xml.attrib['d']
    except KeyError:
        return ""

    svg_xml.attrib.clear()

    if style_str:
        svg_xml.attrib['style'] = style_str

    svg_xml.attrib['d'] = d_attr

    return ET.tostring(svg_xml, encoding='unicode')

type Numeric = Union[int, float]


