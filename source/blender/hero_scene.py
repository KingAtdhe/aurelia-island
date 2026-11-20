"""Concept-art scene for the hero buildings: a city street at golden hour (or night), rendered in Cycles.
python3 hero_scene.py -- OUTDIR [day|night] [samples] [width] [shots]"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; MODE = a[1] if len(a) > 1 else 'day'; SAMP = int(a[2]) if len(a) > 2 else 64; WID = int(a[3]) if len(a) > 3 else 1600
SHOTS = a[4].split(',') if len(a) > 4 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
import isle_lib as L; L.OUT = OUT; os.makedirs(OUT, exist_ok=True)
import isle_props as P, isle_hero as H, isle_life as LF
from mathutils import Vector
P.PREFIX = 'PROP_'
M = H.hero_materials(P.materials()); scn = bpy.context.scene

X = {}; x = 0.0
for name, fn in (('A', H.building_A), ('B', H.building_B), ('C', H.building_C), ('D', H.building_D)):
    K = P.Part(); w = fn(K, M, x); ob, nt = P.make_prop('HERO_' + name, K.arrays()); X[name] = (x, w); print('HERO', name, nt, 'tris'); x += w + 0.05
X1 = x
H.finish_atlas()
# ---------------------------------------------------------------- street: pavements, kerbs, road, opposite pavement
def slab(name, x0, x1, y0, y1, z0, z1, mat, col, uvs=2.0):
    K = P.Part(); K.obj(P.bbox((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, x1 - x0, y1 - y0, z1 - z0), mat, col, 'box', uvs); P.make_prop(name, K.arrays())
pave = L.new_mat('Pave', 0.8, image=L.make_image('pave_ph', np.clip(__import__('isle_photo').colour('PavingStones070', 0.62, 0.6), 0, 1)) if os.path.exists(os.path.join(os.path.dirname(__file__), 'photo', 'PavingStones070_Color.raw')) else None, vcol=True)
asph = L.new_mat('Asph', 0.75, image=L.make_image('asph_ph', np.clip(__import__('isle_photo').colour('Asphalt010', 0.32, 0.4), 0, 1)) if os.path.exists(os.path.join(os.path.dirname(__file__), 'photo', 'Asphalt010_Color.raw')) else None, vcol=True)
slab('Pavement', -30, X1 + 30, -4.6, 0.0, 0.0, 0.15, pave, (0.9, 0.88, 0.84), 2.5)
slab('Kerb', -30, X1 + 30, -4.8, -4.6, 0.0, 0.16, M['stone'], (0.85, 0.84, 0.8))
slab('Road', -60, X1 + 60, -16.8, -4.8, -0.05, 0.0, asph, (0.6, 0.6, 0.62), 6.0)
slab('Kerb2', -30, X1 + 30, -17.0, -16.8, 0.0, 0.16, M['stone'], (0.85, 0.84, 0.8))
slab('Pavement2', -30, X1 + 30, -21.6, -17.0, 0.0, 0.15, pave, (0.9, 0.88, 0.84), 2.5)
K = P.Part()                                                                                         # lane markings
for xx in np.arange(-50, X1 + 50, 6.0): K.obj(P.bbox(xx, -10.8, 0.005, 3.0, 0.15, 0.01), M['smooth'], (0.92, 0.92, 0.88))
for xx in np.arange(-50, X1 + 50, 0.1): pass
K.obj(P.bbox(X1 / 2, -5.15, 0.005, X1 + 100, 0.12, 0.01), M['smooth'], (0.92, 0.92, 0.88)); K.obj(P.bbox(X1 / 2, -16.45, 0.005, X1 + 100, 0.12, 0.01), M['smooth'], (0.92, 0.92, 0.88))
P.make_prop('Markings', K.arrays())
# opposite side backdrop: simple far buildings so the street feels enclosed in the shots that look across
import isle_city as CI
rng = np.random.default_rng(5); xb = -20.0
while xb < X1 + 20:
    w = float(rng.uniform(14, 22)); h = float(rng.uniform(14, 30)); K = P.Part()
    CI.building(K, M, 14.0, w, h, ['brick', 'plaster', 'loft', 'plaster'][int(rng.integers(4))], rng); ob, _ = P.make_prop('Opp_%d' % int(xb), K.arrays())
    ob.location = (xb + w / 2, -21.6 - 7.2, 0); ob.rotation_euler = (0, 0, 0); xb += w + 1.0

# ---------------------------------------------------------------- props from the game kit
LF.register()
lib = P.build(M, ['lamp', 'bench', 'bin', 'hydrant', 'bollard', 'planter', 'cafe', 'scooter', 'bikerack', 'person_0', 'person_1', 'person_2', 'person_3', 'tcar_a', 'tcar_b', 'tcar_c', 'tcar_d', 'tcar_e', 'newsbox', 'trashbags'])
for e in lib.values():
    for k in ('lod0', 'lod1'):
        if e.get(k): e[k].hide_render = True; e[k].hide_viewport = True
CARCOL = [(0.55, 0.06, 0.05), (0.08, 0.18, 0.42), (0.85, 0.85, 0.83), (0.12, 0.13, 0.14), (0.45, 0.47, 0.5), (0.9, 0.7, 0.1)]
def put(name, x, y, yaw, tint=None, z=0.15):
    src = lib[name]['lod0']; ob = src.copy(); ob.data = src.data.copy() if tint else src.data; scn.collection.objects.link(ob); ob.hide_render = False; ob.hide_viewport = False
    ob.location = (x, y, z); ob.rotation_euler = (0, 0, yaw)
    if tint:
        for m in ob.data.materials: pass
        ca = ob.data.color_attributes[0] if ob.data.color_attributes else None
        if ca:
            for d in ca.data:
                c = d.color
                if c[0] > 0.9 and c[1] > 0.9 and c[2] > 0.9: d.color = (tint[0], tint[1], tint[2], 1)
    return ob
for xx in np.arange(4, X1, 14.0): put('lamp', xx, -4.1, math.pi / 2); put('lamp', xx + 7, -17.5, -math.pi / 2)
put('cafe', 3.5, -2.6, 0.3); put('cafe', 7.0, -2.8, 1.2); put('person_1', 5.2, -2.2, 2.4); put('person_3', 2.0, -3.4, -0.6)
put('bench', 30.0, -3.6, -math.pi / 2); put('bin', 32.0, -3.8, 0); put('person_0', 36, -1.5, 1.7); put('planter', 42, -0.9, 0); put('planter', 44.5, -0.9, 0)
put('bikerack', 56, -3.4, 0); put('scooter', 62, -3.8, 0.2, (0.85, 0.15, 0.12)); put('newsbox', 70, -0.6, math.pi); put('hydrant', 77.5, -4.0, 0)
put('person_2', 82, -2.4, 0.4); put('trashbags', 96, -0.8, 0.5); put('scooter', 99, -3.9, -0.1, (0.15, 0.3, 0.6)); put('person_0', 88, -1.2, -2.2)
for i, (xx, nm, ln) in enumerate(((10, 'tcar_b', -6.6), (24, 'tcar_d', -6.6), (47, 'tcar_a', -6.6), (64, 'tcar_c', -6.6), (93, 'tcar_e', -6.6), (18, 'tcar_a', -14.8), (58, 'tcar_b', -14.8), (84, 'tcar_d', -14.8))):
    put(nm, xx, ln, 0.0 if ln < -10 else math.pi, CARCOL[i % len(CARCOL)], 0.0)
# trees in pavement pits
import isle_flora as FL, isle_trees as TRS
bh = FL.bark_height()
FM = dict(bark=L.new_mat('Bark', 0.9, image=L.make_image('bark', np.repeat(bh[..., None], 3, 2) * 0.9 + 0.1), vcol=True), leaf=L.new_mat('Leaves', 1.0, image=L.make_image('leaf_atlas', FL.leaf_atlas()), vcol=True, double=True, cutout=True),
          painted=L.new_mat('PF', 0.8, vcol=True), rock=L.new_mat('RF', 0.9, vcol=True))
try: TRS.render_material(FM['leaf'])
except Exception as e: print('leaf mat', e)
fl = FL.build_library(FM, ['oak'])
src = fl['oak']['lod0']; src.hide_render = True; fl['oak']['lod1'].hide_render = True
for xx in (26.0, 52.0, 79.5, -6.0, X1 + 2):
    t = src.copy(); scn.collection.objects.link(t); t.hide_render = False; t.location = (xx, -3.2, 0.15); t.scale = (0.62, 0.62, 0.62); t.rotation_euler = (0, 0, xx)

# ---------------------------------------------------------------- light, sky, camera
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
sun = bpy.data.lights.new('sun', 'SUN'); so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
if MODE == 'day':
    try:
        sk = nt.nodes.new('ShaderNodeTexSky'); nt.links.new(sk.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.35
        sk.sun_elevation = math.radians(16); sk.sun_rotation = math.radians(205)
    except Exception as e: print('sky', e); bg.inputs[0].default_value = (0.55, 0.68, 0.9, 1); bg.inputs[1].default_value = 1.0
    sun.energy = 4.2; sun.color = (1.0, 0.82, 0.62); sun.angle = math.radians(1.5); so.rotation_euler = (math.radians(74), 0, math.radians(-35))
    scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [l.name for l in []] else 'None'
else:
    bg.inputs[0].default_value = (0.012, 0.02, 0.045, 1); bg.inputs[1].default_value = 1.0
    sun.energy = 0.08; sun.color = (0.6, 0.7, 1.0); so.rotation_euler = (math.radians(50), 0, math.radians(-30))
    for m in bpy.data.materials:
        if m.get('night_emit') and m.node_tree: m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = m['night_emit'] * 6
        if m.name in ('KitLens',) and m.node_tree:
            b = m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Strength'].default_value = 8.0
    for xx in np.arange(4, X1, 14.0):
        for (lx, ly) in ((xx, -4.1 - 1.2), (xx + 7, -17.5 + 1.2)):
            pl = bpy.data.lights.new('l', 'POINT'); pl.energy = 1600; pl.color = (1.0, 0.78, 0.5); pl.shadow_soft_size = 0.3
            po = bpy.data.objects.new('l', pl); po.location = (lx, ly, 7.6); scn.collection.objects.link(po)
    for nm, (x0, w_) in X.items():                                                                  # warm light spilling from the shops
        for xx in np.arange(x0 + 2, x0 + w_ - 1, 4.0):
            al = bpy.data.lights.new('s', 'AREA'); al.energy = 260; al.size = 3.0; al.color = (1.0, 0.75, 0.45)
            ao = bpy.data.objects.new('s', al); ao.location = (xx, 0.4, 2.2); ao.rotation_euler = (math.radians(90), 0, 0); scn.collection.objects.link(ao)
    win = bpy.data.materials.get('KitWindow')
    if win and win.node_tree:                                                                       # random rooms lit: one random value per window-sized cell
        wt = win.node_tree; b = wt.nodes['Principled BSDF']
        gp = wt.nodes.new('ShaderNodeNewGeometry'); vo = wt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 0.42
        wt.links.new(gp.outputs['Position'], vo.inputs['Vector'])
        sep = wt.nodes.new('ShaderNodeSeparateColor'); wt.links.new(vo.outputs['Color'], sep.inputs['Color'])
        cr = wt.nodes.new('ShaderNodeMath'); cr.operation = 'GREATER_THAN'; cr.inputs[1].default_value = 0.58; wt.links.new(sep.outputs[0], cr.inputs[0])
        mu = wt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 3.2; wt.links.new(cr.outputs[0], mu.inputs[0])
        wt.links.new(mu.outputs[0], b.inputs['Emission Strength'])
        tint = wt.nodes.new('ShaderNodeMixRGB'); tint.inputs[1].default_value = (1.0, 0.68, 0.36, 1); tint.inputs[2].default_value = (0.85, 0.9, 1.0, 1)
        wt.links.new(sep.outputs[1], tint.inputs[0]); wt.links.new(tint.outputs[0], b.inputs['Emission Color'])
    cur = bpy.data.materials.get('HeroCurtain')
    if cur and cur.node_tree:
        ct = cur.node_tree; b = ct.nodes['Principled BSDF']; gp = ct.nodes.new('ShaderNodeNewGeometry'); vo = ct.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 0.35
        ct.links.new(gp.outputs['Position'], vo.inputs['Vector']); sep = ct.nodes.new('ShaderNodeSeparateColor'); ct.links.new(vo.outputs['Color'], sep.inputs['Color'])
        g = ct.nodes.new('ShaderNodeMath'); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = 0.5; ct.links.new(sep.outputs[0], g.inputs[0])
        mu = ct.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 2.0; ct.links.new(g.outputs[0], mu.inputs[0])
        b.inputs['Emission Color'].default_value = (0.9, 0.95, 1.0, 1); ct.links.new(mu.outputs[0], b.inputs['Emission Strength'])
    for m in bpy.data.materials:
        if m.get('night_emit') and m.node_tree: m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = m['night_emit'] * 14
    scn.view_settings.view_transform = 'AgX'; scn.view_settings.exposure = -0.9
scn.render.engine = 'CYCLES'; scn.cycles.samples = SAMP; scn.cycles.use_denoising = True
try: scn.cycles.device = 'CPU'
except Exception: pass
cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); scn.collection.objects.link(co); scn.camera = co
scn.render.resolution_x = WID; scn.render.resolution_y = int(WID * 0.5625)
SH = {'A': ((X['A'][0] + 11, 0, 11), (X['A'][0] - 7, -19, 2.2), 32), 'B': ((X['B'][0] + 12, 0, 19), (X['B'][0] + 30, -15.5, 2.2), 22), 'C': ((X['C'][0] + 13, 0, 15), (X['C'][0] + 34, -15.5, 1.8), 20),
      'D': ((X['D'][0] + 11, 0, 10), (X['D'][0] + 27, -19.5, 4.5), 30), 'street': ((X1 * 0.55, 0, 10), (-14, -11, 3.5), 26)}
for k, (tgt, pos, lens) in SH.items():
    if SHOTS and k not in SHOTS: continue
    co.location = pos; cam.lens = lens; d = Vector(tgt) - Vector(pos); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, '%s_%s.png' % (k, MODE)); bpy.ops.render.render(write_still=True); print('SHOT', k)
