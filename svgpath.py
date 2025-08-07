import freetype as ft
from matplotlib.path import Path as MPLPath
from matplotlib.transforms import Affine2D
from shapely.geometry import Polygon, LinearRing
from typing import Optional, Self, Union, Annotated, Iterable
from utils import *
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class BBox:
    xmin: Numeric
    xmax: Numeric
    ymin: Numeric
    ymax: Numeric

@dataclass
class Point:
    x: Numeric
    y: Numeric

class PathBuilder():
    
    @classmethod
    def from_outline(cls, outline) -> Self:
        pb = cls()
        outline.decompose(move_to=pb._move_to,
                          line_to=pb._line_to,
                          conic_to=pb._conic_to,
                          cubic_to=pb._cubic_to)
        return pb
        
    @classmethod
    def from_shapely(cls, shape) -> Self:
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
            point = Point(*linearring.coords[0])
            self._move_to(point)
        for coord in linearring.coords[1:]:
            point = Point(*coord)
            self._line_to(point)


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

class GlyphPathBase(ABC):
    @abstractmethod
    def transform(self, t: Annotated[Iterable[Numeric], 6]) -> Self:
        pass

    @abstractmethod
    def scale(self, xfact:Numeric=1, yfact:Numeric=1) -> Self:
        pass

    @abstractmethod
    def translate(self, xoff:Numeric=0, yoff:Numeric=0) -> Self:
        pass

    @abstractmethod
    def bbox(self) -> BBox:
        pass

    @abstractmethod
    def svg(self, attributes: Optional[dict]=None) -> str:
        pass

    @abstractmethod
    def buffer(self, distance: Numeric, **kwargs) -> Self:
        pass

    @abstractmethod
    def shapely_polygon(self) -> Union[Polygon, MultiPolygon]:
        pass

class GlyphPathEmpty(GlyphPathBase):
    def transform(self, t: Annotated[Iterable[Numeric], 6]) -> Self:
        return type(self)()

    def scale(self, xfact:Numeric=1, yfact:Numeric=1) -> Self:
        return type(self)()

    def translate(self, xoff:Numeric=0, yoff:Numeric=0) -> Self:
        return type(self)()

    def bbox(self) -> BBox:
        return BBox(0, 0, 0, 0)

    def svg(self, attributes: Optional[dict]=None) -> str:
        return ""

    def buffer(self, distance: Numeric, **kwargs) -> Self:
        return type(self)()

    def shapely_polygon(self) -> Union[Polygon, MultiPolygon]:
        return Polygon()

class GlyphPath(GlyphPathBase):
    svg_template = """<path {} d="{}" />"""

    @classmethod
    def from_outline(cls, outline: ft.Outline):
        path_builder = PathBuilder.from_outline(outline)
        path = path_builder.get_path()

        if path:
            return GlyphPath(path)
        else:
            return GlyphPathEmpty()
        
    @classmethod
    def from_shapely(cls, shape: Union[Polygon, MultiPolygon], inverted:bool=False):
        path_builder = PathBuilder.from_shapely(shape)

        path = path_builder.get_path()

        if path:
            return GlyphPath(path, inverted)
        else:
            return GlyphPathEmpty()

    def __init__(self, path:MPLPath, inverted:bool=False):
        # we're using matplptlib.path.Path as the internal representation of the path
        self._path = path
        self._inverted = inverted
    
    def transform(self, t: Annotated[Iterable[Numeric], 6]) -> Self:

        # transform the path per the following affine transform
        # a  b  c
        # d  e  f
        # 0  0  1

        a, b, c, d, e, f = t

        new_inverted = self._inverted

        # if any of a, b, d, e are negative then the polygons become inverted and cw becomes ccw and ccw becomes cw.
        for factor in [a, b, d, e]:
            if factor < 0:
                new_inverted = not new_inverted

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

        return type(self)(self._path.transformed(transform), inverted=new_inverted)
    

    def scale(self, xfact: Numeric=1.0, yfact: Numeric=1.0):
        return self.transform([xfact, 0, 0, 0, yfact, 0])
    
    def translate(self, xoff:Numeric=0, yoff:Numeric=0):
        return self.transform([1, 0, xoff, 0, 1, yoff])

    def bbox(self) -> BBox:
        mpl_bbox = self._path.get_extents()

        return BBox(xmin=mpl_bbox.xmin,
                    xmax=mpl_bbox.xmax,
                    ymin=mpl_bbox.ymin,
                    ymax=mpl_bbox.ymax)

    def _mpl_path(self) -> MPLPath:
        return self._path

    def svg(self, attributes: Optional[dict]=None) -> str:

        if attributes is None:
            attributes = {"stroke": "red",
                          "stroke-width": 2,
                          "fill": None}
        
        # assemble string per xml standard key1="value1" key2="value2"
        attributes_str = " ".join([f'{k}="{v}"' for k, v in attributes.items()])

        # matplotlib path and SVG both use the same internal logical format of move/line/quadratic/cubic
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

    def buffer(self, distance: Numeric, **kwargs):
        shapely_representation = self.shapely_polygon()
        buffered = shapely_representation.buffer(distance=distance, **kwargs)
        return type(self).from_shapely(buffered, self._inverted)

    def shapely_polygon(self) -> Union[Polygon, MultiPolygon]:
        # MPL path to_polygons returns a list of list of coordinates
        if self._path:
            coord_list = self._path.to_polygons()
        else:
            coord_list = []

        polygons = []
        for coords in coord_list:
            # make a shapely LinearRing so we can test direction
            lr = LinearRing(coords) # type:ignore

            # TrueType font spec: clockwise contours are outlines, anti-clockwise contours are holes.
            # Any anti-clockwise contour is a hole for the previous clockwise contour.
            if ((not self._inverted) and lr.is_ccw) or (self._inverted and (not lr.is_ccw)):
                # this coord list is for an interior hole belonging to the previous exterior

                # get the previous polygon (the pevious exterior, with any interiors)
                previous_polygon = polygons[-1]

                # add this hole to the previous polygon
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

    # gp = gp.transform([1, 0, -gp.bbox().xmin,0, 1, -gp.bbox().ymin]) 

    from shapely import BufferJoinStyle as BJS

    if True:
        import matplotlib.pyplot as plt
        from shapely.plotting import plot_polygon
        from itertools import chain
        from shapely import BufferCapStyle as BCS


        cap_styles  = [('round',  BCS.round),
                       ('square', BCS.square),
                       ('flat',   BCS.flat)]
        join_styles = [('round',  BJS.round),
                       ('mitre',  BJS.mitre),
                       ('bevel',  BJS.bevel)]             
        styles = [(x, y) for x in cap_styles for y in join_styles]

        fig, axs = plt.subplots(nrows=3, ncols=3)
        
        for ((cap_desc, cap), (join_desc, join)), ax in zip(styles, chain.from_iterable(axs)):
            ax.axis('equal')   
            plot_polygon(gp.shapely_polygon(), ax=ax, add_points=False, facecolor="#345ca1")
            plot_polygon(gp.shapely_polygon().buffer(-500, cap_style=cap, join_style=join), ax=ax, add_points=False, facecolor="#f9c932")
            ax.set_title(f'cap_style={cap_desc} join_style={join_desc}')
        fig.show()


    if True:
        a = gp.shapely_polygon()
        
        b = GlyphPath.from_shapely(a)

        scale = 0.05
        b = b.transform([scale, 0, b.bbox().xmin*scale, 0, -scale, b.bbox().ymax*scale])


        svg_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="{b.bbox().xmax}" height="{b.bbox().ymax}">
            {b.svg(attributes={"fill": "rgb(52, 92, 161)"})}
            {b.buffer(-25, join_style=BJS.mitre).svg(attributes={"fill": "rgb(249, 201, 50)"})}
        </svg>
        """

        with open("glyphtest.svg", "w") as f:
            f.write(svg_template)

    pass #exists to put a breakpoint on so gp can be interrogated


