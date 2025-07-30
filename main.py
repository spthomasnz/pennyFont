import freetype
from utils import *
from shapely.affinity import translate, scale
from typing import List
from svgpath import GlyphPath

face = freetype.Face("pokemon_solid-webfont.ttf")  # type:ignore

text =  [x for x in "Mr & Mrs Fok Van Der Lee" if x!= " "]


dpi = 96
dpmm = dpi / 25.4

text_height_mm = 150
scale_factor = 1
initial_size = (text_height_mm / scale_factor) * dpmm

advance_scale = 1.5

face.set_char_size(int(initial_size))

y_spacing = 1 * dpmm

inner_paths = []
outer_paths = []
x_pos: List[Numeric] = [0]
max_height = 0
for letter in text:

    face.load_char(letter,
                   freetype.FT_LOAD_DEFAULT |  # type:ignore
                   freetype.FT_LOAD_NO_BITMAP)  # type: ignore

    # get desired glyph from face
    glyph = GlyphPath.from_outline(face.glyph.outline)

    outer_poly = glyph.shapely()
    
    #shift the descender to baseline (0)
    outer_poly = translate(outer_poly, yoff=-face.size.ascender)

    outer_poly = scale(outer_poly, yfact=-1.0, origin=(0, 0))

    # SVG has origin (0, 0) at the top left corner, so everything neds to be flipped in y and then shifted back to positive coordinates
    # outer_poly = invert_y_svg(glyph_outline)

    # generate the smaller inner polygon
    inner_poly = outer_poly.buffer(-15)

    # scale down
    outer_poly = scale(outer_poly, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    inner_poly = scale(inner_poly, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))

    minx, miny, maxx, maxy = outer_poly.bounds
    outer_poly = translate(outer_poly, xoff=x_pos[-1])
    inner_poly = translate(inner_poly, xoff=x_pos[-1])

    
    max_height = max(maxy, max_height)

    x_pos.append(x_pos[-1] + (face.glyph.advance.x * scale_factor * advance_scale))

    outer_paths.append(outer_poly)
    inner_paths.append(inner_poly)

# inner_paths = [translate(inner, yoff=max_height + y_spacing) for inner in inner_paths]
# max_height = max([poly.bounds[3] for poly in inner_paths])

from shapely import union_all

inner = union_all(inner_paths)
outer = union_all(outer_paths)

svg_paths = [poly_to_svg(outer, style={"fill": "rgb(52, 92, 161)"}), poly_to_svg(inner, style={"fill": "rgb(249, 201, 50)"})]

svg = "\n\t".join(svg_paths)

svg_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{outer_paths[-1].bounds[2]/dpmm}mm" height="{max_height/dpmm}mm">
    {svg}
</svg>
"""


with open("glyph.svg", "w") as f:
    f.write(svg_template)


print("SVG written.")
print(f"Width:  {outer_paths[-1].bounds[2]/dpmm} mm")
print(f"Height: {max_height/dpmm} mm")