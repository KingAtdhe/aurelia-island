"""Preview render of the plant library: python3 flora_preview.py -- out [clay]"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isle_lib as L, isle_flora as FL
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--') + 1]; CLAY = 'clay' in sys.argv; L.OUT = '/tmp'
bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene


def materials():
    bh = FL.bark_height(); bark_img = L.make_image('bark', np.repeat(bh[..., None], 3, 2) * 0.9 + 0.1); bark_n = L.nmap('bark_n', bh, 5.0)
    leaf_img = L.make_image('leaf_atlas', FL.leaf_atlas())
    m = dict(bark=L.new_mat('Bark', 0.9, image=bark_img, vcol=True, normal=bark_n), leaf=L.new_mat('Leaves', 1.0, image=leaf_img, vcol=True, double=True, cutout=True),
             painted=L.new_mat('PaintedFlora', 0.8, vcol=True, double=True), rock=L.new_mat('RockFlora', 0.9, vcol=True))
    return m


def leaf_render_material(mat):
    nt = mat.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']; col = nt.nodes['Mix'].outputs[2]; rnd = nt.nodes['Math'].outputs[0]
    for l in list(b.inputs['Alpha'].links): nt.links.remove(l)
    b.inputs['Alpha'].default_value = 1.0
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); nt.links.new(col, tl.inputs['Color'])
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs[0].default_value = 0.35; nt.links.new(b.outputs[0], m1.inputs[1]); nt.links.new(tl.outputs[0], m1.inputs[2])
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); m2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(rnd, m2.inputs[0]); nt.links.new(tp.outputs[0], m2.inputs[1]); nt.links.new(m1.outputs[0], m2.inputs[2]); nt.links.new(m2.outputs[0], out.inputs['Surface'])


M = materials(); leaf_render_material(M['leaf'])
for k_ in ('leaf', 'bark'):
    try: M[k_].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.08
    except Exception as e: print(e)
lib = FL.build_library(M)
order = ['spruce', 'spruce_b', 'pine', 'spruce_snow', 'oak', 'oak_b', 'birch', 'palm', 'cypress', 'fruit', 'cactus', 'bush', 'rock', 'sandstone_spire', 'grass_tall', 'flowers_red']
x = 0
for nm in order:
    e = lib[nm]; w = max(e['lod0'].dimensions[0], 2.0); x += w / 2 + 1.0; e['lod0'].location = (x, 0, 0)
    e['lod1'].location = (x, 16, 0); x += w / 2 + 1.0
    print('%-14s LOD0 %5d tris   LOD1 %5d tris   height %.1f' % (nm, e['t0'], e['t1'], e['h']))
for nm, e in lib.items():
    if nm not in order: e['lod0'].hide_render = True; e['lod1'].hide_render = True
tot = x
me = bpy.data.meshes.new('g'); me.from_pydata([(-60, -60, 0), (tot + 60, -60, 0), (tot + 60, 90, 0), (-60, 90, 0)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new('g', me); scn.collection.objects.link(g); gm = L.new_mat('g', 0.95, color=(0.16, 0.22, 0.09)); me.materials.append(gm)
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.7, 1.0, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 4.0; sun.angle = 0.03; so = bpy.data.objects.new('s', sun); scn.collection.objects.link(so); so.rotation_euler = (math.radians(52), 0, math.radians(35))
if CLAY:
    clay = L.new_mat('clay', 0.7, color=(0.6, 0.6, 0.6)); scn.view_layers[0].material_override = clay
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = tot + 4; co = bpy.data.objects.new('c', cam); scn.collection.objects.link(co)
co.location = (tot / 2, -80, 22); co.rotation_euler = (Vector((tot / 2, 4, 8.5)) - Vector(co.location)).to_track_quat('-Z', 'Y').to_euler(); scn.camera = co
scn.render.engine = 'CYCLES'; scn.cycles.samples = int(os.environ.get("SAMP", 40)); scn.cycles.use_denoising = True; scn.render.resolution_x = 2400; scn.render.resolution_y = 760
scn.render.image_settings.file_format = 'JPEG'; scn.render.filepath = os.path.abspath(os.path.join(OUT, 'flora_%s.jpg' % ('clay' if CLAY else 'beauty')))
try: scn.view_settings.view_transform = 'AgX'
except Exception: pass
bpy.ops.render.render(write_still=True)
