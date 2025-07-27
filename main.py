import freetype
from utils import *
from shapely.affinity import translate, scale

face = freetype.Face("pokemon_solid-webfont.ttf")  # type:ignore

text =  [x for x in "Mr & Mrs Fok Van Der Lee" if x != " "]

initial_size = 1500
scale_factor = 0.1

x_spacing = 1

svg_paths = []
x_pos = 0
max_height = 0
for letter in text:

    glyph = GlyphToSVGPath(face=face,
                           size=initial_size,
                           char=letter)

    outer_poly = invert_y_svg(glyph.to_shapely())
    inner_poly = outer_poly.buffer(-30)

    outer_poly = scale(outer_poly, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    inner_poly = scale(inner_poly, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))

    minx, miny, maxx, maxy = outer_poly.bounds
    width = maxx - minx
    outer_poly = translate(outer_poly, xoff=x_pos)
    inner_poly = translate(inner_poly, xoff=x_pos)

    height = maxy - miny
    max_height = max(height, max_height)

    x_pos += width + x_spacing

    svg_paths.append("\n\t".join([poly_to_svg(outer_poly, style={"fill": "rgb(52, 92, 161)"}),
                                  poly_to_svg(inner_poly, style={"fill": "rgb(249, 201, 50)"})]))



svg = "\n\t".join(svg_paths)


svg_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{x_pos - x_spacing}" height="{max_height}">
    {svg}
</svg>
"""


with open("glyph.svg", "w") as f:
    f.write(svg_template)
