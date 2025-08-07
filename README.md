# pennyFont
A couple of scripts to generate text with a smaller (internal) border for laser cutting.

## GlyphPath
`glyphpath.py` contains the class `GlyphPath`, which has constructors from freetype outlines or shapely Polygons/MultiPolygons.

### Constructors
`GlyphPath.from_outline` uses matplotlib.path to generate real coordinates for glyphs that use cubic or quadratic bezier curves.
`GlyphPath.from_shapely` just takes a shapely Polygon/MultiPolygon and stores it in the internal format.
`GlyphPath` should never be instantiated directly (i.e. via calling `GlyphPath(...)`)

### Methods
#### scale/translate/transform
The methods `scale`, `translate`, and `transform` each return a new `GlyphPath` instance of the glyph with the requested transformation applied.

#### shapely_polygon
The method `shapely_polygon` returns a shapely Polygon/Multipolygon representation of the glyph.

#### buffer
The method `buffer` returns a new `GlyphPath` instance with shapely.buffer applied to the glyph. `kwargs` are passed directly to `shapely.buffer`

#### svg
The method `svg` returns an SVG path representation of the glyph. The dict argument `attributes` is used as the attributes of the svg path.
Don't forget that the origin of an SVG is at the top-left, so glyphs will need to be inverted in the y-axis to be the correct orientation.

## `main.py`
See `main.py` for an example of usage of `GlyphPath` in generating a string of text and converting it to SVG for laser cutting.
Also see the `__name__ == "__main__"` section of `glyphpath.py` for an example of join/cap styles in `buffer` on a single glyph.
