import freetype
import itertools
from typing import Union, Optional

type Numeric = Union[int, float]

def minmax(it) -> tuple[Numeric, Numeric]:
    min = max = None
    for val in it:
        if min is None or val < min:
            min = val
        if max is None or val > max:
            max = val

    if min is None or max is None:
        raise ValueError
    return min, max

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def transform(self, t):
        a, b, c, d, e, f = t

        new_x = a*self.x + b*self.y + c
        new_y = d*self.x + e*self.y + f

        self.x = new_x
        self.y = new_y


class SVGMoveBase(object):
    def __init__(self) -> None:
        raise NotImplementedError

    def svg_move(self) -> str:
        raise NotImplementedError

    def transform(self, t) -> None:
        raise NotImplementedError

    def x_coords(self):
        raise NotImplementedError

    def y_coords(self):
        raise NotImplementedError


class SVGMoveTo(SVGMoveBase):
    def __init__(self, a):
        self.a = a

    def transform(self, t):
        self.a.transform(t)

    def svg_move(self):
        return f"M {self.a.x:.3f},{self.a.y:.3f}"

    def x_coords(self):
        return [self.a.x]

    def y_coords(self):
        return [self.a.y]


class SVGLineTo(SVGMoveBase):
    def __init__(self, a):
        self.a = a

    def transform(self, t):
        self.a.transform(t)

    def svg_move(self):
        return f"L {self.a.x:.3f},{self.a.y:.3f}"

    def x_coords(self):
        return [self.a.x]

    def y_coords(self):
        return [self.a.y]


class SVGConicTo(SVGMoveBase):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def transform(self, t):
        self.a.transform(t)
        self.b.transform(t)

    def svg_move(self):
        return f"Q {self.a.x:.3f},{self.a.y:.3f} {self.b.x:.3f},{self.b.y:.3f}"

    def x_coords(self):
        return [self.a.x, self.b.x]

    def y_coords(self):
        return [self.a.y, self.b.y]


class SVGCubicTo(SVGMoveBase):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def transform(self, t):
        self.a.transform(t)
        self.b.transform(t)
        self.c.transform(t)

    def svg_move(self):
        return f"C {self.a.x:.3f},{self.a.y:.3f} {self.b.x:.3f},{self.b.y:.3f} {self.c.x:.3f},{self.c.y:.3f}"

    def x_coords(self):
        return [self.a.x, self.b.x, self.c.x]

    def y_coords(self):
        return [self.a.y, self.b.y, self.c.y]


class GlyphToSVGPath(object):

    svg_template = """<path style="{}" d="{}" />"""

    def __init__(self, face, size, char, style: Optional[dict]=None):
        
        face.set_char_size(size)

        face.load_char(char, freetype.FT_LOAD_DEFAULT | #type:ignore
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

    def get_style(self):
        return " ".join([f"{k}:{v};" for k, v in self.style.items()])

    def get_moves(self):
        return " ".join([m.svg_move() for m in self.moves]) + " Z"

    def move_to(self, a, _):
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
        x_min, x_max = minmax(itertools.chain(*[move.x_coords() for move in self.moves]))
        y_min, y_max = minmax(itertools.chain(*[move.y_coords() for move in self.moves]))
        return (x_min, x_max, y_min, y_max)

    def svg_path(self):
        return self.svg_template.format(self.get_style(), self.get_moves())


if __name__ == '__main__':
    face = freetype.Face('pokemon_solid-webfont.ttf')

    outer_glyph = GlyphToSVGPath(face=face,
                                 size=500,
                                 char="S",
                                 style={"fill": "rgb(52, 92, 161)", 'stroke': 'none'})

    # invert y
    outer_glyph.transform([1, 0, 0, 0, -1, 0])

    # shift minimum bounds to origin
    x_min, x_max, y_min, y_max = outer_glyph.bbox()   
    outer_glyph.transform([1, 0, -x_min, 0, 1, -y_min])



    svg_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg xmlns="http://www.w3.org/2000/svg">
            {}
    </svg>
    """
    svg = (svg_template.format(outer_glyph.svg_path()))

    with open("glyph.svg", "w") as f:
        f.write(svg)
