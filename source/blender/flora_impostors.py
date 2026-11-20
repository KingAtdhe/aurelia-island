"""Renders the far-distance tree impostor atlas from the modelled trees, so far and near trees match.
python3 flora_impostors.py -- out      -> out/tree_atlas_src.npy (1024 x 2048 RGBA, row 0 at the bottom)"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isle_lib as L, isle_flora as FL, isle_trees as TRS
from mathutils import Vector
OUT = sys.argv[sys.argv.index('--') + 1]; L.OUT = '/tmp'; N = 512
bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene
bh = FL.bark_height()
M = dict(bark=L.new_mat('Bark', 0.9, image=L.make_image('bark', np.repeat(bh[..., None], 3, 2) * 0.9 + 0.1), vcol=True), leaf=L.new_mat('Leaves', 1.0, image=L.make_image('leaf_atlas', FL.leaf_atlas()), vcol=True, double=True, cutout=True),
         painted=L.new_mat('P', 0.8, vcol=True), rock=L.new_mat('R', 0.9, vcol=True))
TRS.render_material(M['leaf'])
names = ['spruce', 'spruce_b', 'oak', 'spruce_snow', 'birch', 'palm']; lib = FL.build_library(M, names)
for e in lib.values(): e['lod0'].hide_render = True; e['lod1'].hide_render = True
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.8, 0.88, 1.0, 1); bg.inputs[1].default_value = 1.7
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 3.6; sun.angle = 0.5; so = bpy.data.objects.new('s', sun); scn.collection.objects.link(so)
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; co = bpy.data.objects.new('c', cam); scn.collection.objects.link(co); scn.camera = co
scn.render.engine = 'CYCLES'; scn.cycles.samples = 40; scn.cycles.use_denoising = True; scn.cycles.transparent_max_bounces = 64; scn.render.film_transparent = True
scn.render.resolution_x = scn.render.resolution_y = N; scn.render.image_settings.file_format = 'PNG'; scn.render.image_settings.color_mode = 'RGBA'; scn.view_settings.view_transform = 'Standard'
ASP = [0.66, 0.66, 1.3, 0.5, 1.0, 0.9]; atlas = np.zeros((2 * N, 4 * N, 4))


def shot(name, side, cell, aspect):
    e = lib[name]; o = e['lod0']; o.hide_render = False; h = e['h']
    if side:
        wd_ = max(o.dimensions.x, o.dimensions.y); cam.ortho_scale = max(h, wd_ / aspect * 1.02); scn.render.pixel_aspect_x = 1.0 / aspect if aspect < 1 else 1.0; scn.render.pixel_aspect_x = 1.0
        # non-square view: the card is narrower than it is tall, so squeeze the tree sideways into the square cell
        o.scale = (1 / aspect, 1 / aspect, 1); co.location = (0, -60, cam.ortho_scale / 2); co.rotation_euler = (math.radians(90), 0, 0); so.rotation_euler = (math.radians(50), 0, math.radians(25))
    else:
        o.scale = (1, 1, 1); wd = max(h * aspect * 0.96, max(o.dimensions.x, o.dimensions.y) * 1.02); cam.ortho_scale = wd; co.location = (0, 0, h + 20); co.rotation_euler = (0, 0, 0); so.rotation_euler = (math.radians(20), 0, 0)
    scn.render.filepath = '/tmp/imp_%d.png' % cell; bpy.ops.render.render(write_still=True); o.hide_render = True; o.scale = (1, 1, 1)
    im = bpy.data.images.load(scn.render.filepath); px = np.array(im.pixels[:]).reshape(N, N, 4); bpy.data.images.remove(im)
    a = px[..., 3] > 0.45; rgb = px[..., :3].copy()
    if a.any():
        lum = rgb[a].mean(); rgb = rgb * min(3.0, 0.2 / max(lum, 1e-3))          # art sheet 04 trees: bring each card to the same overall brightness as the near models in game light
        rgb[~a] = rgb[a].mean(0)
    r, c = cell // 4, cell % 4; atlas[r * N:(r + 1) * N, c * N:(c + 1) * N, :3] = rgb; atlas[r * N:(r + 1) * N, c * N:(c + 1) * N, 3] = a


for k, nm in enumerate(names): shot(nm, True, k, ASP[k])
shot('spruce', False, 6, 0.5); shot('oak', False, 7, 0.98)
np.save(os.path.join(OUT, 'tree_atlas_src.npy'), atlas.astype(np.float32))
from PIL import Image
Image.fromarray((np.clip(atlas[::-1], 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'atlas_preview.png'))
