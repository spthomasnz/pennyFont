import freetype
from matplotlib.path import Path as MPLPath
from matplotlib.transforms import Affine2D
from shapely.geometry import Polygon
from typing import Optional
from utils import *

class PathBuilder():
    def __init__(self, outline):
        self._vertices = []
        self._codes = []

        outline.decompose(move_to=self._move_to,
                          line_to=self._line_to,
                          conic_to=self._conic_to,
                          cubic_to=self._cubic_to)

    def _move_to(self, a, _):
        if self._vertices:
            self._vertices.append((0, 0))
            self._codes.append(MPLPath.CLOSEPOLY)

        self._vertices.append((a.x, a.y))
        self._codes.append(MPLPath.MOVETO)

    def _line_to(self, a, _):
        self._vertices.append((a.x, a.y))
        self._codes.append(MPLPath.LINETO)

    def _conic_to(self, a, b, _):
        self._vertices.append((a.x, a.y))
        self._vertices.append((b.x, b.y))
        self._codes.extend([MPLPath.CURVE3]*2)

    def _cubic_to(self, a, b, c, _):
        self._vertices.append((a.x, a.y))
        self._vertices.append((b.x, b.y))
        self._vertices.append((c.x, c.y))
        self._codes.extend([MPLPath.CURVE4]*3)

    def get_path(self):
        return MPLPath(vertices=self._vertices, codes=self._codes)

class GlyphPath(object):
    svg_template = """<path {} d="{}" />"""

    @classmethod
    def from_outline(cls, outline: freetype.Outline):
        path_builder = PathBuilder(outline)
        return cls(path_builder.get_path())

    def __init__(self, path):
        self._path = path
    
    def transform(self, t):

        # transform the path per the following affine transform
        # a  b  c
        # d  e  f
        # 0  0  1

        a, b, c, d, e, f = t

        # MPL uses a different order of [af] than I do, so translate
        # a  c  e
        # b  d  f
        # 0  0  1
        transform = Affine2D.from_values(a=a,
                                         b=d,
                                         c=b,
                                         d=e,
                                         e=c,
                                         f=f)

        return type(self)(self._path.transformed(transform))

    def bbox(self):
        return self._path.get_extents()

    def mpl_path(self):
        return self._path

    def svg(self, attributes: Optional[dict]=None):

        if attributes is None:
            attributes = {"stroke": "red",
                          "stroke-width": 2,
                          "fill": None}

        attributes_str = " ".join([f'{k}="{v}"' for k, v in attributes.items()])

        moves = []

        for vertices, code in self._path.iter_segments():
        
            match code:
                case MPLPath.MOVETO:
                    x, y = vertices
                    moves.append(f"M {x:.3f}, {y:.3f}")
                case MPLPath.LINETO:
                    x, y = vertices
                    moves.append(f"L {x:.3f}, {y:.3f}")
                case MPLPath.CURVE3:
                    xc, yc, x, y = vertices
                    moves.append(f"Q {xc:.3f}, {yc:.3f}, {x:.3f}, {y:.3f}")
                case MPLPath.CURVE4:
                    xc1, yc1, xc2, yc2, x, y = vertices
                    moves.append(f"Q {xc1:.3f}, {yc1:.3f}, {xc2:.3f}, {yc2:.3f}, {x:.3f}, {y:.3f}")
                case MPLPath.CLOSEPOLY:
                    moves.append("Z")

        return self.svg_template.format(attributes_str, " ".join(moves))

    def shapely(self):
        shapes = self._path.to_polygons()

        if shapes:
            return Polygon(shell=shapes[0],   #  type:ignore
                           holes=shapes[1:])  #  type:ignore
        else:
            return Polygon()


if __name__ == "__main__":

    face = freetype.Face("pokemon_solid-webfont.ttf")
    face.set_char_size(15000)
    face.load_char("8",
                freetype.FT_LOAD_DEFAULT |   # type:ignore
                freetype.FT_LOAD_NO_BITMAP)  # type: ignore

    outline = face.glyph.outline

    gp = GlyphPath.from_outline(outline)

    gp = gp.transform([1, 0, -gp.bbox().xmin,0, 1, -gp.bbox().ymin])

    import matplotlib.pyplot as plt
    from shapely.plotting import plot_polygon
    
    fig, ax = plt.subplots()
    plot_polygon(gp.shapely(), ax=ax)
    fig.show()

    gp_svg = gp.transform([0.1, 0, 0, 0, -0.1, gp.bbox().ymax*0.1])

    svg = '<?xml version="1.0" encoding="UTF-8"?>\n' +\
         f'<svg xmlns="http://www.w3.org/2000/svg" width="{gp_svg.bbox().xmax}" height="{gp_svg.bbox().ymax}">\n' +\
         f'\t{gp_svg.svg()}\n' +\
          '</svg>'

    with open("glyphpath_test.svg", "w") as f:
        f.write(svg)
        

    pass #exists to put a breakpoint on so gp can be interrogated

