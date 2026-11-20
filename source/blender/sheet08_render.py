"""Art sheet 08 tiles (built from the sheet 04 scene): one plant per render, stood on a grass verge in late-afternoon light, Cycles.
python3 sheet04_render.py -- OUTDIR samples size name[,name...] [clay]"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; SAMP = int(a[1]); SIZE = int(a[2]); NAMES = a[3].split(','); CLAY = len(a) > 4 and a[4] == 'clay'
os.makedirs(OUT, exist_ok=True)
import isle_lib as L, isle_flora as FL, isle_trees_hq as TH, flora_atlas_hq as FA, isle_photo as PH, isle_props as KP, isle_roads_hq as RQ, isle_wild_hq as WQ, isle_props_hq as HQP, isle_hero as HR
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
    bc = nt.nodes.new('ShaderNodeHueSaturation'); bc.inputs['Value'].default_value = 2.5; nt.links.new(mx.outputs[2], bc.inputs['Color']); nt.links.new(bc.outputs[0], b.inputs['Base Color'])
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
r = np.random.default_rng(3)
gob, _, _ = build('grass_hq'); fob, _, _ = build('flowers_hq'); SCAT = []
for k in range(1400):
    x, y = r.uniform(-26, 26), r.uniform(-10, 34)
    if math.hypot(x, y) < 1.2: continue
    src = fob if r.random() < 0.1 else gob; o = src.copy(); o.location = (x, y, 0); o.rotation_euler = (0, 0, r.uniform(0, 6.3)); s = r.uniform(0.9, 1.5); o.scale = (s, s, s); scn.collection.objects.link(o)
    SCAT.append((o, math.hypot(x, y)))
gob.hide_render = fob.hide_render = True
for k in range(70):                                                                 # distant tree line behind the subject
    sp_ = ['oak', 'plane', 'birch', 'spruce'][k % 4]; ob, _, _ = build(sp_, r.uniform(-90, 90), r.uniform(70, 110), r.uniform(0, 6.3), lod=1, scale=r.uniform(0.8, 1.2)); SCAT.append((ob, 999))
SAND = L.new_mat('Sand', 0.95, image=L.make_image('sand', np.clip(PH.colour('Ground080', 0.62, 0.7) * np.array([0.75, 0.6, 0.42]) / 0.62, 0, 1)))
SAND.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.1
snt = SAND.node_tree; tc2 = snt.nodes.new('ShaderNodeTexCoord'); mp2 = snt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (0.3, 0.3, 0.3)
snt.links.new(tc2.outputs['Object'], mp2.inputs['Vector']); snt.links.new(mp2.outputs['Vector'], [n for n in snt.nodes if n.type == 'TEX_IMAGE'][0].inputs['Vector'])

# ---- light: sky and a warm low sun
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; wn = w.node_tree; bg = wn.nodes['Background']
sk = wn.nodes.new('ShaderNodeTexSky'); wn.links.new(sk.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = float(os.environ.get('SKY', 0.4))
try: sk.sun_elevation = math.radians(30); sk.sun_rotation = math.radians(215 + 90); sk.sun_disc = False
except Exception: pass
lp = wn.nodes.new('ShaderNodeLightPath'); tcw = wn.nodes.new('ShaderNodeTexCoord'); sxyz = wn.nodes.new('ShaderNodeSeparateXYZ'); wn.links.new(tcw.outputs['Window'], sxyz.inputs[0])
rmp = wn.nodes.new('ShaderNodeMapRange'); rmp.inputs['From Min'].default_value = 0.45; rmp.inputs['From Max'].default_value = 1.0; wn.links.new(sxyz.outputs['Y'], rmp.inputs['Value'])
grd = wn.nodes.new('ShaderNodeMix'); grd.data_type = 'RGBA'; grd.inputs[6].default_value = (0.62, 0.76, 0.92, 1); grd.inputs[7].default_value = (0.2, 0.38, 0.75, 1); wn.links.new(rmp.outputs[0], grd.inputs[0])
bgc = wn.nodes.new('ShaderNodeBackground'); bgc.inputs['Strength'].default_value = 1.0; wn.links.new(grd.outputs[2], bgc.inputs['Color'])
ms = wn.nodes.new('ShaderNodeMixShader'); wn.links.new(lp.outputs['Is Camera Ray'], ms.inputs[0]); wn.links.new(bg.outputs[0], ms.inputs[1]); wn.links.new(bgc.outputs[0], ms.inputs[2])
wn.links.new(ms.outputs[0], wn.nodes['World Output'].inputs['Surface'])                     # camera sees a clean blue gradient, the plants are lit by the sky model
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = float(os.environ.get('SUN', 4.8)); sun.color = (1.0, 0.86, 0.7); sun.angle = math.radians(1.2); so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
so.rotation_euler = (math.radians(58), 0, math.radians(215))
scn.render.engine = 'CYCLES'; scn.cycles.samples = SAMP; scn.cycles.use_denoising = True; scn.cycles.max_bounces = 6; scn.cycles.transparent_max_bounces = 128
try: scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Base Contrast'
except Exception: pass
scn.view_settings.exposure = float(os.environ.get('EXPO', -0.45)); scn.render.resolution_x = SIZE; scn.render.resolution_y = SIZE
if CLAY: scn.view_layers[0].material_override = L.new_mat('clay', 0.7, color=(0.62, 0.62, 0.6))
cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); scn.collection.objects.link(co); scn.camera = co; cam.lens = 50

import types
WQ.register(); HQP.register(); KM = HR.hero_materials(KP.materials()); KM['rock'] = KP.mats()['rock']; RQ.register(KM); RQ.register_kit(KM)
CQ = types.SimpleNamespace(ITEMS=dict({'road_' + k: v for k, v in RQ.ITEMS.items()}, **RQ.KIT_ITEMS, rk_island_191=(None, 11.0)))
WATERY = ()
DESERT = ()
wm = bpy.data.materials.new('Sea'); wm.use_nodes = True; wb = wm.node_tree.nodes['Principled BSDF']; wb.inputs['Base Color'].default_value = (0.004, 0.05, 0.065, 1); wb.inputs['Roughness'].default_value = 0.14
nz = wm.node_tree.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 6.0; bp = wm.node_tree.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.45
wm.node_tree.links.new(nz.outputs['Fac'], bp.inputs['Height']); wm.node_tree.links.new(bp.outputs['Normal'], wb.inputs['Normal'])
mew = bpy.data.meshes.new('sea'); mew.from_pydata([(-300, -300, 0), (300, -300, 0), (300, 300, 0), (-300, 300, 0)], [], [(0, 1, 2, 3)]); SEA = bpy.data.objects.new('sea', mew); scn.collection.objects.link(SEA); mew.materials.append(wm)
def build_prop(name, x=0.0, y=0.0, yaw=0.0):
    e = KP.build(KM, [name])[name]; e['lod1'].hide_render = True; ob = e['lod0']; ob.location = (x, y, 0); ob.rotation_euler = (0, 0, yaw)
    return ob, e['t0'], 0
stats = {}
for nm in NAMES:
    groups = [(nm, 0, 0, 0.0, 1)] if nm in CQ.ITEMS else {'roadside': [('guardrail_hq', 0, 0, 0.0, 1)]}.get(nm) or {'meadow': [('grass_hq', 0, 0, 0, 1.4), ('flowers_hq', 0.6, 0.3, 1, 1.4), ('flowers_hq', -0.5, -0.4, 2, 1.2), ('grass_hq', 0.3, -0.8, 3, 1.2), ('flowers_hq', -0.9, 0.6, 4, 1.3)],
              'shrubs': [('oleander', -1.3, 0.4, 0, 1), ('hedge', 1.6, 0.6, 0.0, 1), ('laurel', 0.2, -1.2, 1, 1)],
              'understory': [('fern', 0, 0, 0, 1.2), ('fern', 1.3, 0.6, 1, 0.9), ('log', -0.4, 1.4, 0.4, 1), ('fern', -1.4, -0.3, 2, 1.0)],
              'desert': [('agave', -0.9, 0, 0, 1.2), ('prickly_pear', 1.1, 0.5, 0, 1), ('agave', 0.4, -1.2, 1, 0.7)]}.get(nm, [(nm, 0, 0, 0.0, 1)])
    scn.view_settings.exposure = (-1.1 if nm in WATERY else float(os.environ.get('EXPO', -0.45))); bg.inputs['Strength'].default_value = (0.22 if nm in WATERY else float(os.environ.get('SKY', 0.4)))
    small = True; g.data.materials[0] = SAND if nm in DESERT else gm; wet = nm in WATERY; g.location.z = -0.06; SEA.hide_render = not wet
    for o, dist in SCAT: o.hide_render = (nm in DESERT) or wet or (dist < 999 and dist < 14) or False
    obs = []; tri = 0
    for sp_, x, y, yaw, s in groups:
        ob, tb, tl = build_prop(sp_, x, y, yaw) if (sp_ in CQ.ITEMS and not obs.append(None) and obs.pop() is None) else build(sp_, x, y, yaw, scale=s, lod=int(os.environ.get('LOD', 0))); obs.append(ob); tri += tb + tl
    bpy.context.view_layer.update()
    bb0 = np.array([list(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box]); lo0, hi0 = bb0.min(0) - 0.6, bb0.max(0) + 0.6
    for o, dist in SCAT:
        if dist < 999: o.hide_render = bool(lo0[0] < o.location.x < hi0[0] and lo0[1] < o.location.y < hi0[1])
    bb = np.array([list(o.matrix_world @ Vector(c)) for o in obs for c in o.bound_box]); lo, hi = bb.min(0), bb.max(0); h = hi[2]; wd = max(hi[0] - lo[0], hi[1] - lo[1])
    s = max(h, wd * 0.62); tgt = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.6)); d = s * (1.6 if nm == 'road_hairpin' else 1.25) + 1.2
    co.location = tgt + (Vector((-d * 0.62, -d * 0.62, d * 0.55)) if nm.startswith('rk_') and nm != 'rk_island_191' else Vector((d * 0.62, -d * 0.62, d * 0.55))); co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, '%s%s.png' % (nm, '_clay' if CLAY else '')); bpy.ops.render.render(write_still=True)
    stats[nm] = dict(tris=tri, height=round(float(h), 1)); print('TILE', nm, stats[nm])
    for o in obs: o.hide_render = True
import json; json.dump(stats, open(os.path.join(OUT, 'stats%s.json' % ('_clay' if CLAY else '')), 'w'))
