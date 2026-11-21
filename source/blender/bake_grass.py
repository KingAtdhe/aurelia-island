"""Grass clump atlas for the game, from the concept 13 blade models: 4 kinds (lush, dry, verge, dune) x 2 variants, each 256x256 with alpha,
rendered orthographic from the side under soft even light (the game lights them). Writes OUT/grass_atlas.png (2048x256)."""
import sys, os
OUTD = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp/grassbake'
sys.argv = ['x', '--', OUTD, 'meadow', '1', '8', '8']
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sheet13_render.py')).read().split("TILES = dict(")[0]
exec(src)
import numpy as np
from PIL import Image
os.makedirs(OUTD, exist_ok=True)
KINDS = [('lush', 1.0), ('lush', 1.25), ('dry', 1.0), ('dry', 1.2), ('verge', 1.0), ('short', 1.6), ('dune', 0.8), ('dune', 1.0)]
class Flat:                       # flat ground for drop()
    def ray_cast(self, o, d): return (Vector((o.x, o.y, 0.0)), None, None, None)
tiles = []
for i, (k, sc) in enumerate(KINDS):
    for o in list(scn.objects): bpy.data.objects.remove(o, do_unlink=True)
    rng_ = np.random.default_rng(100 + i)
    pts = [(rng_.normal(0, 0.09), rng_.normal(0, 0.03)) for _ in range(9 if k != 'dune' else 6)]
    ob = grass('clump', Flat(), pts, k, BLADE, sc)
    if i in (0, 1): flowers('fl', Flat(), [(rng_.normal(0, 0.08), 0.0) for _ in range(2)], [(0.95, 0.95, 0.9), (0.95, 0.8, 0.15)])
    w = bpy.data.worlds.new('W'); scn.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.6
    cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 0.62; co = bpy.data.objects.new('cam', cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (0, -2.0, 0.3); co.rotation_euler = (math.radians(90), 0, 0)
    scn.render.engine = 'CYCLES'; scn.cycles.samples = 48; scn.cycles.use_denoising = True; scn.render.resolution_x = scn.render.resolution_y = 256; scn.render.film_transparent = True
    scn.view_settings.view_transform = 'Standard'; scn.render.image_settings.color_mode = 'RGBA'
    f = os.path.join(OUTD, 'g%d.png' % i); scn.render.filepath = f; bpy.ops.render.render(write_still=True); tiles.append(f)
atlas = Image.new('RGBA', (256 * len(tiles), 256))
for i, f in enumerate(tiles): atlas.paste(Image.open(f).convert('RGBA'), (i * 256, 0))
a = np.asarray(atlas).astype(np.float32); al = a[..., 3:] / 255.0
rgb = np.where(al > 0.02, a[..., :3] / np.maximum(al, 1e-3), 0)                  # un-premultiply, then bleed colour into the transparent texels (no dark fringes)
from scipy import ndimage
m = al[..., 0] > 0.3; idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
rgb = rgb[idx[0], idx[1]]
out = np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8)
Image.fromarray(out, 'RGBA').save(os.path.join(OUTD, 'grass_atlas.png')); print('ATLAS', os.path.join(OUTD, 'grass_atlas.png'))
