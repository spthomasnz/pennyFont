import freetype
from glyphpath import GlyphPath

face = freetype.Face("pokemon_solid-webfont.ttf")  # type:ignore

text =  "SPHINX OF BLACK QUARTZ, JUDGE MY VOW".lower()

dpi = 96
dpmm = dpi / 25.4

text_height_mm = 150
scale_factor = 1
initial_size = (text_height_mm / scale_factor) * dpmm

advance_scale = 1.0

face.set_char_size(int(initial_size))

y_spacing = 1 * dpmm

inner_paths = []
outer_paths = []
x_pos = [0]
for letter in text:
    face.load_char(letter,
                   freetype.FT_LOAD_DEFAULT |  # type:ignore
                   freetype.FT_LOAD_NO_BITMAP)  # type: ignore

    # get desired glyph from face
    outer_glyph = GlyphPath.from_outline(face.glyph.outline)

    # shift the ascender to baseline (0) - this puts y coordinated into negative
    outer_glyph = outer_glyph.translate(yoff=-face.size.ascender)

    # SVG has origin (0, 0) at the top left corner, so everything needs to be flipped in y
    outer_glyph = outer_glyph.scale(yfact=-1.0)

    # generate the smaller inner polygon
    inner_glyph = outer_glyph.buffer(-25)

    # scale down
    outer_glyph = outer_glyph.scale(xfact=scale_factor, yfact=scale_factor)
    inner_glyph = inner_glyph.scale(xfact=scale_factor, yfact=scale_factor)

    bounds = outer_glyph.bbox
    outer_glyph = outer_glyph.translate(xoff=x_pos[-1])
    inner_glyph = inner_glyph.translate(xoff=x_pos[-1])

    x_pos.append(x_pos[-1] + (face.glyph.advance.x * scale_factor * advance_scale))

    outer_paths.append(outer_glyph)
    inner_paths.append(inner_glyph)


outer_max_height = max([x.bbox.ymax for x in outer_paths])
# inner_paths = [inner.translate(yoff=outer_max_height + y_spacing) for inner in inner_paths]

inner_max_height = max([x.bbox.ymax for x in inner_paths])

max_height = max(inner_max_height, outer_max_height)

group_template = """
<g>
    {}
    {}
</g>
""".strip()

svg = "\n\t".join([group_template.format(outer.svg(attributes={"fill": "rgb(52, 92, 161)"}), inner.svg(attributes={"fill": "rgb(249, 201, 50)"})) for inner, outer in zip(inner_paths, outer_paths) if type(outer) is GlyphPath])


svg_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{outer_paths[-1].bbox.xmax/dpmm}mm" height="{max_height/dpmm}mm">
    {svg}
</svg>
"""

with open("glyph.svg", "w") as f:
    f.write(svg_template)

print("SVG written.")
print(f"Width:  {outer_paths[-1].bbox.xmax/dpmm} mm")
print(f"Height: {max_height/dpmm} mm")
