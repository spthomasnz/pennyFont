import os
import sys

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import freetype

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

    def get_str(self):
        raise NotImplementedError

    def transform(self, t):
        raise NotImplementedError

class SVGMoveTo(SVGMoveBase):
    def __init__(self):
        pass

    def transform(self, t):
        pass


class GlyphToSVGPath(object):

    svg_template = """<path style="fill:none;stroke:#000000;stroke-width:2;" d="{}" />"""

    def __init__(self, outline: freetype.Outline, offset=(0, 0)):
        self.moves = []

        self.outline = outline

        bbox = outline.get_bbox()

        self.width = bbox.xMax - bbox.xMin
        self.x_offset = -bbox.xMin + offset[0]

        self.y_max = bbox.yMax

        outline.decompose(move_to=self.move_to,
                          line_to=self.line_to,
                          conic_to=self.conic_to,
                          cubic_to=self.cubic_to)

    def move_to(self, a, _):
        self.moves.append("M {},{}".format(a.x + self.x_offset, self.y_max - a.y))

    def line_to(self, a, _):
        self.moves.append("L {},{}".format(a.x + self.x_offset, self.y_max - a.y))

    def conic_to(self, a, b, _):
        self.moves.append("Q {},{} {},{}".format(a.x + self.x_offset, self.y_max - a.y, b.x + self.x_offset, self.y_max - b.y))

    def cubic_to(self, a, b, c, _):
        self.moves.append("C {},{} {},{} {},{}".format(a.x + self.x_offset, self.y_max - a.y, b.x + self.x_offset, self.y_max - b.y, c.x + self.x_offset, self.y_max - c.y))

    def path(self):
        return self.svg_template.format(" ".join(self.moves))


if __name__ == '__main__':
    face = freetype.Face('pokemon_solid-webfont.ttf')
    face.set_char_size(18*64)
    face.load_char('T', freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)

    a = GlyphToSVGPath(face.glyph.outline)

    svg_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg xmlns="http://www.w3.org/2000/svg">
      <g>
        {}
      </g>
    </svg>
    """


    with open("glyph.svg", "w") as f:
        f.write(svg_template.format(a.path()))

