import freetype as ft
from matplotlib.path import Path as MPLPath
from matplotlib.transforms import Affine2D
from shapely.geometry import Polygon, LinearRing
from typing import Optional, Self, Union
from utils import *
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
import contextlib
import ctypes

@dataclass
class BBox:
    xmin: Numeric
    xmax: Numeric
    ymin: Numeric
    ymax: Numeric

class PathBuilder():
    
    @classmethod
    def from_outline(cls, outline):
        pb = cls()
        outline.decompose(move_to=pb._move_to,
                          line_to=pb._line_to,
                          conic_to=pb._conic_to,
                          cubic_to=pb._cubic_to)
        return pb
        
    @classmethod
    def from_shapely(cls, shape):
        pb = cls()

        if type(shape) is Polygon:
            pb._process_polygon(shape)
        elif type(shape) is MultiPolygon:
            for polygon in shape.geoms:
                pb._process_polygon(polygon)

        return pb
      

    def _process_polygon(self, polygon):
        self._process_linearring(polygon.exterior)
        for interior in polygon.interiors:
            self._process_linearring(interior)
    
    def _process_linearring(self, linearring):
        if linearring.coords[:1]:
            self._move_to(linearring.coords[0])
        for coord in linearring.coords[1:]:
            self._line_to(coord)


    def __init__(self):
        self._vertices = []
        self._codes = []

    def _move_to(self, a, _=None):
        if self._vertices:
            self._vertices.append((0, 0))
            self._codes.append(MPLPath.CLOSEPOLY)

        self._vertices.append((a.x, a.y))
        self._codes.append(MPLPath.MOVETO)

    def _line_to(self, a, _=None):
        self._vertices.append((a.x, a.y))
        self._codes.append(MPLPath.LINETO)

    def _conic_to(self, a, b, _=None):
        self._vertices.append((a.x, a.y))
        self._vertices.append((b.x, b.y))
        self._codes.extend([MPLPath.CURVE3]*2)

    def _cubic_to(self, a, b, c, _=None):
        self._vertices.append((a.x, a.y))
        self._vertices.append((b.x, b.y))
        self._vertices.append((c.x, c.y))
        self._codes.extend([MPLPath.CURVE4]*3)

    def get_path(self):
        if self._vertices:
            return MPLPath(vertices=self._vertices, codes=self._codes)
        else:
            return None

class GlyphPath(ABC):
    svg_template = """<path {} d="{}" />"""

    class representations(Enum):
        MPL_PATH = 1
        SHAPELY_POLY = 2
        EMPTY = 3

    @classmethod
    def from_outline(cls, outline: ft.Outline):
        path_builder = PathBuilder.from_outline(outline)
        return GlyphPathMPL(path_builder.get_path())
    
    @classmethod
    def from_shapely(cls, shape: Union[Polygon, MultiPolygon]):
        pass
        # vertices = 

    @classmethod
    def _from_shapely_polygon(cls, polygon):
        pass

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def transform(self, t) -> Self:
        pass

    @abstractmethod
    def bbox(self) -> BBox:
        pass

    @abstractmethod
    def mpl_path(self) -> Optional[MPLPath]:
        pass

    @abstractmethod
    def svg(self,attributes: Optional[dict]) -> str:
        pass

    @abstractmethod
    def shapely_polygon(self) -> Union[Polygon, MultiPolygon]:
        pass


class GlyphPathMPL(GlyphPath):
    representation = GlyphPath.representations.MPL_PATH

    def __init__(self, path):
        # we're using matplptlib.path.Path as the internal representation of the path
        self._path = path
    
    def transform(self, t) -> Self:

        # transform the path per the following affine transform
        # a  b  c
        # d  e  f
        # 0  0  1

        a, b, c, d, e, f = t

        # MPL uses a different order of [abcdef] than I do, so translate
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

    def bbox(self) -> BBox:
        mpl_bbox = self._path.get_extents()

        return BBox(xmin=mpl_bbox.xmin,
                    xmax=mpl_bbox.xmax,
                    ymin=mpl_bbox.ymin,
                    ymax=mpl_bbox.ymax)

    def mpl_path(self) -> MPLPath:
        return self._path

    def svg(self, attributes: Optional[dict]=None) -> str:

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

    def shapely_polygon(self):
        # MPL path to_polygons returns a list of list of coordinates
        if self._path:
            coord_list = self._path.to_polygons()
        else:
            coord_list = []

        polygons = []
        for coords in coord_list:
            # make a shapely LinearRing so we can test direction
            lr = LinearRing(coords)

            # TrueType font spec: clockwise contours are outlines, anti-clockwise contours are holes.
            # Any anti-clockwise contour is a hole for the previous clockwise contour.
            if lr.is_ccw:
                # this coord list is for an interior hole belonging to the previous exterior

                # get the previous polygon (the pevious exterior, with any interiors)
                previous_polygon = polygons[-1]


                polygons[-1] = Polygon(shell=previous_polygon.exterior,
                                       holes = list(previous_polygon.interiors) + [lr])
            else:
                # this coord list is for a new exterior
                polygons.append(Polygon(lr))
        
        if len(polygons) == 0:
            return Polygon()
        elif len(polygons) == 1:
            return polygons[0]
        else:
            return MultiPolygon(polygons)
        
if __name__ == "__main__":

    face = ft.Face("pokemon_solid-webfont.ttf")
    face.set_char_size(15000)
    face.load_char("8",
                ft.FT_LOAD_DEFAULT |   # type:ignore
                ft.FT_LOAD_NO_BITMAP)  # type: ignore

    outline = face.glyph.outline

    gp = GlyphPath.from_outline(outline)

    gp = gp.transform([1, 0, -gp.bbox().xmin,0, 1, -gp.bbox().ymin]) 

    import matplotlib.pyplot as plt
    from shapely.plotting import plot_polygon
    fig, ax = plt.subplots()
    ax.axis('equal')   
    plot_polygon(gp.shapely_polygon(), ax=ax, add_points=False, facecolor="#345ca1")
    plot_polygon(gp.shapely_polygon().buffer(-500,), ax=ax, add_points=False, facecolor="#f9c932")

    fig.show()

    pass #exists to put a breakpoint on so gp can be interrogated


