"""Art sheet 15 tiles: the concept 04 trees at game weight (LOD 2, what the Godot game would draw up close), stood on the
verge of an asphalt road and seen from the road, in late-afternoon light, Cycles. HERO=1 renders a wide roadside view.
python3 sheet15_render.py -- OUTDIR samples size name[,name...]"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; SAMP = int(a[1]); SIZE = int(a[2]); NAMES = a[3].split(','); CLAY = len(a) > 4 and a[4] == 'clay'
os.makedirs(OUT, exist_ok=True)
import isle_lib as L, isle_flora as FL, isle_trees_hq as TH, flora_atlas_hq as FA, isle_photo as PH
from mathutils import Vector

_IMG = {}
def img(name, arr, raw=False):
    if name not in _IMG: _IMG[name] = L.make_image(name, arr[::-1].copy(), raw=raw)                 # numpy rows top-down -> Blender bottom-up
    return _IMG[name]


def leaf_material():
    m = bpy.data.materials.new('LeavesHQ'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img('leaf_atlas_hq', FA.atlas()); tx.interpolation = 'Cubic'
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    nt.links.new(vc.outputs['Color'], mx.inputs[6]); nt.links.new(tx.outputs['Color'], mx.inputs[7])
    bc = nt.nodes.new('ShaderNodeHueSaturation'); bc.inputs['Value'].default_value = 3.1; nt.links.new(mx.outputs[2], bc.inputs['Color']); nt.links.new(bc.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    try: b.inputs['Specular IOR Level'].default_value = 0.25
    except Exception: pass
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); br = nt.nodes.new('ShaderNodeBrightContrast'); br.inputs['Bright'].default_value = 0.05
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1.25; hs.inputs['Value'].default_value = 1.3
    nt.links.new(mx.outputs[2], hs.inputs['Color']); nt.links.new(hs.outputs[0], tl.inputs['Color'])
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs[0].default_value = 0.5; nt.links.new(b.outputs[0], m1.inputs[1]); nt.links.new(tl.outputs[0], m1.inputs[2])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.4; nt.links.new(tx.outputs['Alpha'], gt.inputs[0])
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); m2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gt.outputs[0], m2.inputs[0]); nt.links.new(tp.outputs[0], m2.inputs[1]); nt.links.new(m1.outputs[0], m2.inputs[2]); nt.links.new(m2.outputs[0], out.inputs['Surface'])
    return m


def bark_material(kind):
    c, h = FA.bark(kind)
    return L.new_mat('Bark_' + kind, 0.85, image=img('bark_' + kind, c), vcol=True, normal=L.nmap('bark_n_' + kind, h[::-1].copy(), 6.0), nstrength=1.2)


bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene
LEAF = leaf_material(); PAINT = L.new_mat('PlantPaint', 0.85, vcol=True)
try: PAINT.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
except Exception: pass
BARKS = {}
def build(name, x=0.0, y=0.0, yaw=0.0, lod=0, scale=1.0):
    fn, kw, bk = TH.SPECIES[name]; b, l, h = fn(lod=lod, **kw)
    if bk and bk not in BARKS: BARKS[bk] = bark_material(bk)
    parts = []
    if b is not None and b.V: parts.append((b, BARKS[bk] if bk else PAINT))
    if l is not None and l.V: parts.append((l, LEAF))
    ob = FL.make_object('HQ_%s' % name, parts); ob.data.attributes.remove(ob.data.attributes['custom_normal'])   # render with true card normals: Cycles flips them per side, translucency does the rest
    ob.location = (x, y, 0); ob.rotation_euler = (0, 0, yaw); ob.scale = (scale,) * 3
    return ob, b.tris() if b is not None else 0, l.tris() if l is not None else 0

# ---- ground: photo grass with a dirt patch, scattered grass and flower clumps
gimg = PH.colour('Grass004', 0.55, 0.7) * np.array([0.15, 0.27, 0.045]) / 0.55; gm = L.new_mat('Ground', 0.95, image=L.make_image('ground', np.clip(gimg, 0, 1)))
for m_ in (gm,):
    try: m_.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.08
    except Exception: pass
nt = gm.node_tree; tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.25, 0.25, 0.25)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0].inputs['Vector'])
me = bpy.data.meshes.new('g'); me.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)]); g = bpy.data.objects.new('g', me); scn.collection.objects.link(g); me.materials.append(gm)
# ---- the road: photo asphalt 7 m wide along y at x = -5.5, white edge lines, a gravel shoulder
AS = L.new_mat('Asphalt', 0.8, image=L.make_image('asph', np.clip(PH.colour('Asphalt010', 0.11, 0.4), 0, 1)))
ant = AS.node_tree; tc3 = ant.nodes.new('ShaderNodeTexCoord'); mp3 = ant.nodes.new('ShaderNodeMapping'); mp3.inputs['Scale'].default_value = (0.4, 0.4, 0.4)
ant.links.new(tc3.outputs['Object'], mp3.inputs['Vector']); ant.links.new(mp3.outputs['Vector'], [n for n in ant.nodes if n.type == 'TEX_IMAGE'][0].inputs['Vector'])
def slab(nm, x0, x1, z, mat):
    m_ = bpy.data.meshes.new(nm); m_.from_pydata([(x0, -60, z), (x1, -60, z), (x1, 160, z), (x0, 160, z)], [], [(0, 1, 2, 3)]); o_ = bpy.data.objects.new(nm, m_); scn.collection.objects.link(o_); m_.materials.append(mat); return o_
GRV = L.new_mat('Gravel', 0.95, image=L.make_image('grv', np.clip(PH.colour('Gravel022', 0.42, 0.6), 0, 1)))
LINE = L.new_mat('Line', 0.6, color=(0.85, 0.85, 0.82))
slab('shoulder', -2.6, -1.4, 0.015, GRV); slab('road', -9.6, -2.6, 0.03, AS); slab('edge', -2.85, -2.7, 0.035, LINE); slab('edge2', -9.5, -9.35, 0.035, LINE)
ROADX = (-9.8, -1.3)
r = np.random.default_rng(3)
gob, _, _ = build('grass_hq'); fob, _, _ = build('flowers_hq'); SCAT = []
for k in range(1400):
    x, y = r.uniform(-26, 26), r.uniform(-10, 34)
    if math.hypot(x, y) < 1.2 or ROADX[0] < x < ROADX[1]: continue
    src = fob if r.random() < 0.1 else gob; o = src.copy(); o.location = (x, y, 0); o.rotation_euler = (0, 0, r.uniform(0, 6.3)); s = r.uniform(0.9, 1.5); o.scale = (s, s, s); scn.collection.objects.link(o)
    SCAT.append((o, math.hypot(x, y)))
gob.hide_render = fob.hide_render = True
for k in range(70):                                                                 # distant tree line behind the subject
    sp_ = ['oak', 'plane', 'birch', 'spruce'][k % 4]; ob, _, _ = build(sp_, r.choice([r.uniform(-90, -14), r.uniform(4, 90)]), r.uniform(70, 110), r.uniform(0, 6.3), lod=1, scale=r.uniform(0.8, 1.2)); SCAT.append((ob, 999))
SAND = L.new_mat('Sand', 0.95, image=L.make_image('sand', np.clip(PH.colour('Ground080', 0.62, 0.7) * np.array([0.75, 0.6, 0.42]) / 0.62, 0, 1)))
SAND.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.1
snt = SAND.node_tree; tc2 = snt.nodes.new('ShaderNodeTexCoord'); mp2 = snt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (0.3, 0.3, 0.3)
snt.links.new(tc2.outputs['Object'], mp2.inputs['Vector']); snt.links.new(mp2.outputs['Vector'], [n for n in snt.nodes if n.type == 'TEX_IMAGE'][0].inputs['Vector'])

# ---- light: sky and a warm low sun
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; wn = w.node_tree; bg = wn.nodes['Background']
sk = wn.nodes.new('ShaderNodeTexSky'); wn.links.new(sk.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.75
try: sk.sun_elevation = math.radians(30); sk.sun_rotation = math.radians(215 + 90); sk.sun_disc = False
except Exception: pass
lp = wn.nodes.new('ShaderNodeLightPath'); tcw = wn.nodes.new('ShaderNodeTexCoord'); sxyz = wn.nodes.new('ShaderNodeSeparateXYZ'); wn.links.new(tcw.outputs['Window'], sxyz.inputs[0])
rmp = wn.nodes.new('ShaderNodeMapRange'); rmp.inputs['From Min'].default_value = 0.45; rmp.inputs['From Max'].default_value = 1.0; wn.links.new(sxyz.outputs['Y'], rmp.inputs['Value'])
grd = wn.nodes.new('ShaderNodeMix'); grd.data_type = 'RGBA'; grd.inputs[6].default_value = (0.62, 0.76, 0.92, 1); grd.inputs[7].default_value = (0.2, 0.38, 0.75, 1); wn.links.new(rmp.outputs[0], grd.inputs[0])
bgc = wn.nodes.new('ShaderNodeBackground'); bgc.inputs['Strength'].default_value = 1.0; wn.links.new(grd.outputs[2], bgc.inputs['Color'])
ms = wn.nodes.new('ShaderNodeMixShader'); wn.links.new(lp.outputs['Is Camera Ray'], ms.inputs[0]); wn.links.new(bg.outputs[0], ms.inputs[1]); wn.links.new(bgc.outputs[0], ms.inputs[2])
wn.links.new(ms.outputs[0], wn.nodes['World Output'].inputs['Surface'])                     # camera sees a clean blue gradient, the plants are lit by the sky model
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.8; sun.color = (1.0, 0.86, 0.7); sun.angle = math.radians(1.2); so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
so.rotation_euler = (math.radians(58), 0, math.radians(215))
scn.render.engine = 'CYCLES'; scn.cycles.samples = SAMP; scn.cycles.use_denoising = True; scn.cycles.max_bounces = 6; scn.cycles.transparent_max_bounces = 128
try: scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Base Contrast'
except Exception: pass
scn.view_settings.exposure = 0.15; scn.render.resolution_x = SIZE; scn.render.resolution_y = SIZE
if CLAY: scn.view_layers[0].material_override = L.new_mat('clay', 0.7, color=(0.62, 0.62, 0.6))
cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); scn.collection.objects.link(co); scn.camera = co; cam.lens = 50

stats = {}
if os.environ.get('HERO'):          # a wide view down the road: mixed trees on both verges
    scn.render.resolution_x = int(SIZE * 2.3); cam.lens = 30
    rr = np.random.default_rng(11); k = 0
    for y in np.arange(4, 150, 7.5):
        for side in (1, -1):
            sp_ = NAMES[k % len(NAMES)]; k += 1
            x = (rr.uniform(0.5, 4) if side > 0 else rr.uniform(-16, -12.5))
            build(sp_, x, y + rr.uniform(-2, 2), rr.uniform(0, 6.3), lod=2, scale=rr.uniform(0.85, 1.1))
    co.location = Vector((-6.2, -12, 2.2)); co.rotation_euler = (Vector((-5.0, 60, 3.0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, 'hero.png'); bpy.ops.render.render(write_still=True); print('HERO done'); sys.exit(0)
for nm in NAMES:
    groups = {'meadow': [('grass_hq', 0, 0, 0, 1.4), ('flowers_hq', 0.6, 0.3, 1, 1.4), ('flowers_hq', -0.5, -0.4, 2, 1.2), ('grass_hq', 0.3, -0.8, 3, 1.2), ('flowers_hq', -0.9, 0.6, 4, 1.3)],
              'shrubs': [('oleander', -1.3, 0.4, 0, 1), ('hedge', 1.6, 0.6, 0.0, 1), ('laurel', 0.2, -1.2, 1, 1)],
              'understory': [('fern', 0, 0, 0, 1.2), ('fern', 1.3, 0.6, 1, 0.9), ('log', -0.4, 1.4, 0.4, 1), ('fern', -1.4, -0.3, 2, 1.0)],
              'desert': [('agave', -0.9, 0, 0, 1.2), ('prickly_pear', 1.1, 0.5, 0, 1), ('agave', 0.4, -1.2, 1, 0.7)]}.get(nm, [(nm, 0, 0, 0.0, 1)])
    small = nm in ('shrubs', 'understory', 'meadow', 'desert'); g.data.materials[0] = SAND if nm == 'desert' else gm
    for o, dist in SCAT: o.hide_render = (nm == 'desert') or (small and dist < 10 and nm != 'meadow')
    obs = []; tri = 0
    for sp_, x, y, yaw, s in groups:
        ob, tb, tl = build(sp_, x, y, yaw, scale=s, lod=int(os.environ.get('LOD', 0))); obs.append(ob); tri += tb + tl
    bpy.context.view_layer.update()
    bb = np.array([list(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box]); lo, hi = bb.min(0), bb.max(0); h = hi[2]; wd = max(hi[0] - lo[0], hi[1] - lo[1])
    s = max(h, wd * 0.95); tgt = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, h * 0.47)); d = s * 1.55 + 1.2
    co.location = Vector((-5.0, tgt.y - d * 1.05, 1.5)); tgt = Vector((tgt.x - 0.8, tgt.y, h * 0.45))          # from the road, at driving height
    co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, '%s%s.png' % (nm, '_clay' if CLAY else '')); bpy.ops.render.render(write_still=True)
    stats[nm] = dict(tris=tri, height=round(float(h), 1)); print('TILE', nm, stats[nm])
    for o in obs: o.hide_render = True
import json; json.dump(stats, open(os.path.join(OUT, 'stats%s.json' % ('_clay' if CLAY else '')), 'w'))
