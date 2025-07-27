import xml.etree.ElementTree as ET
from shapely.affinity import affine_transform
from typing import Union
import itertools
from typing import Optional
import freetype
from shapely.geometry import Polygon
from SVGMoves import *

# invert y co-ordinates per svg standard of origin being in the top-left corner
def invert_y_svg(poly):
    minx, miny, maxx, maxy = poly.bounds
    return affine_transform(poly, [1, 0, 0, -1, 0, maxy + miny])


def poly_to_svg(poly, style=None):

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


class GlyphToSVGPath(object):
    svg_template = """<path style="{}" d="{}" />"""

    def __init__(self, face, size, char, style: Optional[dict] = None):

        face.set_char_size(size)

        face.load_char(char,
                       freetype.FT_LOAD_DEFAULT |  # type:ignore
                       freetype.FT_LOAD_NO_BITMAP)  # type: ignore

        if style is None:
            self.style = {"fill": "none", 'stroke': 'black', 'stroke-width': 2}
        else:
            self.style = style

        self.moves: list[SVGMoveBase] = []

        self.outline = face.glyph.outline

        self.outline.decompose(move_to=self.move_to,
                               line_to=self.line_to,
                               conic_to=self.conic_to,
                               cubic_to=self.cubic_to)

        self.moves.append(SVGClosePolygon())

        # shift minimum bounds to origin
        x_min, x_max, y_min, y_max = self.bbox()
        self.transform([1, 0, -x_min, 0, 1, -y_min])

    def get_style(self):
        return " ".join([f"{k}:{v};" for k, v in self.style.items()])

    def get_moves(self):
        return " ".join([m.svg_move() for m in self.moves])

    def move_to(self, a, _):
        if self.moves:
            self.moves.append(SVGClosePolygon())

        a_point = Point(a.x, a.y)
        self.moves.append(SVGMoveTo(a_point))

    def line_to(self, a, _):
        a_point = Point(a.x, a.y)
        self.moves.append(SVGLineTo(a_point))

    def conic_to(self, a, b, _):
        a_point = Point(a.x, a.y)
        b_point = Point(b.x, b.y)
        self.moves.append(SVGConicTo(a_point, b_point))

    def cubic_to(self, a, b, c, _):
        a_point = Point(a.x, a.y)
        b_point = Point(b.x, b.y)
        c_point = Point(c.x, c.y)
        self.moves.append(SVGCubicTo(a_point, b_point, c_point))

    def transform(self, t):
        for m in self.moves:
            m.transform(t)

    def bbox(self) -> tuple[Numeric, Numeric, Numeric, Numeric]:
        x_points = itertools.chain(*[move.x_coords() for move in self.moves if move])
        x_min, x_max = minmax(x_points)

        y_points = itertools.chain(*[move.y_coords() for move in self.moves if move])
        y_min, y_max = minmax(y_points)

        return x_min, x_max, y_min, y_max

    def svg_path(self):
        return self.svg_template.format(self.get_style(), self.get_moves())

    def mpl_path(self):
        vertices, codes = zip(*[x.mpl_path() for x in self.moves])

        codes = list(itertools.chain(*codes))
        vertices = list(itertools.chain(*vertices))

        return Path(vertices, codes)

    def to_shapely(self):
        path = self.mpl_path()
        shapes = path.to_polygons()

        return Polygon(shell=shapes[0],
                       holes=shapes[1:])
