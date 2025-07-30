import xml.etree.ElementTree as ET
from shapely.affinity import affine_transform
from typing import Union
from shapely.geometry import MultiPolygon


# invert y co-ordinates per svg standard of origin being in the top-left corner
def invert_y_svg(poly):
    minx, miny, maxx, maxy = poly.bounds
    return affine_transform(poly, [1, 0, 0, -1, 0, maxy + miny])


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

def minmax(it) -> tuple[Numeric, Numeric]:
    local_min = local_max = None
    for val in it:
        if local_min is None or val < local_min:
            local_min = val
        if local_max is None or val > local_max:
            local_max = val

    if local_min is None or local_max is None:
        raise ValueError
    return local_min, local_max


