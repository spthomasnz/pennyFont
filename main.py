import freetype
from utils import *
from shapely.affinity import translate, scale

face = freetype.Face("pokemon_solid-webfont.ttf")  # type:ignore

text =  [x for x in "Mr & Mrs Fok Van Der Lee" if x != " "]

initial_size = 1500
scale_factor = 0.1

x_spacing = 1
y_spacing = 1

inner_paths = []
outer_paths = []
x_pos = [0]
max_height = 0
for letter in text:

    glyph = GlyphToSVGPath(face=face,
                           size=initial_size,
                           char=letter)

    outer_poly = invert_y_svg(glyph.to_shapely())
    inner_poly = outer_poly.buffer(-50)

    outer_poly = scale(outer_poly, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    inner_poly = scale(inner_poly, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))

    minx, miny, maxx, maxy = outer_poly.bounds
    width = maxx - minx
    outer_poly = translate(outer_poly, xoff=x_pos[-1])
    inner_poly = translate(inner_poly, xoff=x_pos[-1])

    height = maxy - miny
    max_height = max(height, max_height)

    x_pos.append(x_pos[-1] + width + x_spacing)

    outer_paths.append(outer_poly)
    inner_paths.append(inner_poly)

inner_paths = [translate(inner, yoff=max_height + y_spacing) for inner in inner_paths]


svg_paths = ["\n\t".join([poly_to_svg(outer, style={"fill": "rgb(52, 92, 161)"}), poly_to_svg(inner, style={"fill": "rgb(249, 201, 50)"})]) for outer, inner in zip(outer_paths, inner_paths)]

svg = "\n\t".join(svg_paths)


svg_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{x_pos[-1] - x_spacing}" height="{max_height*2+y_spacing}">
    {svg}
</svg>
"""


with open("glyph.svg", "w") as f:
    f.write(svg_template)
