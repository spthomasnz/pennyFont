import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon
from itertools import chain
from shapely import BufferCapStyle as BCS
from shapely import BufferJoinStyle as BJS

from pathlib import Path
import sys

parent_folder = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_folder))

from glyphpath import GlyphPath

cap_styles  = [('round',  BCS.round),
                ('square', BCS.square),
                ('flat',   BCS.flat)]
join_styles = [('round',  BJS.round),
                ('mitre',  BJS.mitre),
                ('bevel',  BJS.bevel)]             
styles = [(x, y) for x in cap_styles for y in join_styles]


gp = GlyphPath.from_face("pokemon_solid-webfont.ttf", "8", 15000)

gp = gp.transform([1, 0, -gp.bbox.xmin,0, 1, -gp.bbox.ymin])


fig, axs = plt.subplots(nrows=3, ncols=3)
fig.suptitle("Comparison of cap and join styles for shapely.buffer")

for ((cap_desc, cap), (join_desc, join)), ax in zip(styles, chain.from_iterable(axs)):
    ax.axis('equal')   
    plot_polygon(gp.shapely_polygon(), ax=ax, add_points=False, facecolor="#345ca1")
    plot_polygon(gp.shapely_polygon().buffer(-500, cap_style=cap, join_style=join), ax=ax, add_points=False, facecolor="#f9c932")
    ax.set_title(f'cap_style={cap_desc} join_style={join_desc}')
plt.show(block=True)
