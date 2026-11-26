"""Art sheet 16 tiles: the four city building types of isle_towers_hq on a street corner, seen from the pavement, late
morning sun with a physical sky (the glass reflects it), Cycles. HERO=1: a street lined with all four, from car height.
python3 sheet16_render.py -- OUTDIR samples width height kind[,kind...]"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; SAMP = int(a[1]); W = int(a[2]); H = int(a[3]); KINDS = a[4].split(',')
os.makedirs(OUT, exist_ok=True)
import isle_lib as L, isle_photo as PH, isle_towers_hq as TW
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene

def mat(name, col, rough, metal=0.0, photo=None, scale=0.5, emit=0.0, alpha=1.0, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    try: b.inputs['Specular IOR Level'].default_value = spec
    except Exception: pass
    if photo:
        c = PH.colour(photo, 0.6, 0.5); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = L.make_image('ph_' + name, np.clip(c, 0, 1)); tx.projection = 'BOX'; tx.projection_blend = 0.2
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        mx.inputs[6].default_value = (*[min(1.0, v * 1.6) for v in col], 1); nt.links.new(tx.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    if emit > 0: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    if alpha < 1: b.inputs['Alpha'].default_value = alpha
    return m

M = {
 'Glass': mat('Glass', (0.045, 0.06, 0.075), 0.03, spec=0.9), 'GlassDark': mat('GlassDark', (0.03, 0.035, 0.04), 0.05, spec=0.8),
 'GlassLobby': mat('GlassLobby', (0.35, 0.28, 0.2), 0.08, emit=0.35, spec=0.8), 'GlassCrown': mat('GlassCrown', (0.12, 0.2, 0.26), 0.04, spec=0.9),
 'GlassRail': mat('GlassRail', (0.5, 0.6, 0.62), 0.05, alpha=0.35), 'Alu': mat('Alu', (0.72, 0.74, 0.76), 0.28, metal=1.0),
 'Spandrel': mat('Spandrel', (0.08, 0.085, 0.09), 0.25, metal=0.4), 'Stone': mat('Stone', (0.66, 0.55, 0.4), 0.8, photo='Plaster003', scale=0.35),
 'StoneDark': mat('StoneDark', (0.4, 0.33, 0.25), 0.85, photo='Plaster003', scale=0.5), 'Render': mat('Render', (0.86, 0.83, 0.77), 0.85, photo='Plaster003', scale=0.4),
 'Timber': mat('Timber', (0.4, 0.24, 0.12), 0.6), 'Frame': mat('Frame', (0.82, 0.82, 0.8), 0.4, metal=0.6), 'FrameDark': mat('FrameDark', (0.08, 0.08, 0.085), 0.4, metal=0.6),
 'Coping': mat('Coping', (0.55, 0.55, 0.54), 0.6, metal=0.3), 'Plant': mat('Plant', (0.6, 0.6, 0.58), 0.5, metal=0.4), 'Tank': mat('Tank', (0.5, 0.48, 0.44), 0.6),
 'Louvre': mat('Louvre', (0.35, 0.36, 0.37), 0.4, metal=0.7), 'Core': mat('Core', (0.2, 0.2, 0.2), 0.9), 'Panel': mat('Panel', (0.55, 0.5, 0.46), 0.6, photo='Plaster003', scale=0.6),
 'Slab': mat('Slab', (0.7, 0.7, 0.68), 0.7), 'Band': mat('Band', (0.9, 0.9, 0.88), 0.45), 'Canopy': mat('Canopy', (0.15, 0.16, 0.17), 0.3, metal=0.8),
 'Foliage': mat('Foliage', (0.12, 0.25, 0.06), 0.8), 'CrownLight': mat('CrownLight', (1.0, 0.92, 0.8), 0.3, emit=4.0),
}

def boxes_to_object(name, B, loc=(0, 0, 0), yaw=0.0):
    me = bpy.data.meshes.new(name); verts = []; faces = []; mi = []; mats = list(B.keys())
    for k, m in enumerate(mats):
        for c, s in B[m]:
            c = np.array(c); h = np.array(s) / 2; n0 = len(verts)
            for dx in (-1, 1):
                for dy in (-1, 1):
                    for dz in (-1, 1): verts.append(tuple(c + h * (dx, dy, dz)))
            for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)): faces.append(tuple(n0 + i for i in f)); mi.append(k)
    me.from_pydata(verts, [], faces); me.update()
    for m in mats: me.materials.append(M[m])
    me.polygons.foreach_set('material_index', mi)
    ob = bpy.data.objects.new(name, me); scn.collection.objects.link(ob); ob.location = loc; ob.rotation_euler = (0, 0, yaw)
    return ob, len(faces) * 2

# ---- street: road along x at y = -16..-8, pavements of setts, kerbs
ROAD = mat('Road', (0.1, 0.1, 0.105), 0.75, photo='Asphalt010', scale=0.3); PAVE = mat('Pave', (0.34, 0.32, 0.29), 0.8, photo='PavingStones070', scale=0.4)
def slab(nm, x0, x1, y0, y1, z, m):
    me = bpy.data.meshes.new(nm); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)]); o = bpy.data.objects.new(nm, me); scn.collection.objects.link(o); me.materials.append(m)
slab('road', -400, 400, -40, -14, 0.0, ROAD); slab('pave', -400, 400, -14, 60, 0.15, PAVE); slab('pave2', -400, 400, -80, -40, 0.15, PAVE)
for yy in (-14, -40): boxes_to_object('kerb%d' % yy, {'Coping': [((0, yy, 0.08), (800, 0.3, 0.16))]})
LINE = mat('Line', (0.85, 0.85, 0.82), 0.6); slab('cl', -400, 400, -27.1, -26.9, 0.01, LINE)

# ---- light: physical sky and sun
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; wn = w.node_tree; bg = wn.nodes['Background']
sk = wn.nodes.new('ShaderNodeTexSky'); wn.links.new(sk.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.28
try: sk.sky_type = 'NISHITA'; sk.sun_elevation = math.radians(38); sk.sun_rotation = math.radians(140); sk.sun_disc = False
except Exception: pass
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.color = (1.0, 0.93, 0.84); sun.angle = math.radians(0.8); so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(140 + 90))
scn.render.engine = 'CYCLES'; scn.cycles.samples = SAMP; scn.cycles.use_denoising = True; scn.cycles.max_bounces = 6
try: scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
scn.view_settings.exposure = -0.35; scn.render.resolution_x = W; scn.render.resolution_y = H
cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); scn.collection.objects.link(co); scn.camera = co; cam.lens = 19

def place(kind, x, y, seed=1):
    B, (bw, bd), h = TW.KINDS[kind](seed=seed); return boxes_to_object(kind + str(seed), B, (x, y + bd / 2, 0.15)), h, bw

if os.environ.get('HERO'):
    x = -40.0; k = 0; tris = 0
    while x < 400:
        kd = KINDS[k % len(KINDS)]; (ob, t), h, bw = place(kd, x + 18, 0.0, seed=k + 1); x += bw + 6; k += 1
    x = -40.0; k = 2
    while x < 400:
        kd = KINDS[k % len(KINDS)]; B, (bw, bd), h = TW.KINDS[kd](seed=k + 7); boxes_to_object('s%d' % k, B, (x + 18, -40 - bd / 2, 0.15), math.pi); x += bw + 6; k += 1
    co.location = Vector((-8, -24, 2.4)); co.rotation_euler = (Vector((60, -20, 16)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, 'hero.png'); bpy.ops.render.render(write_still=True); print('HERO done'); sys.exit(0)

import json; stats = {}
for kd in KINDS:
    for o in list(scn.objects):
        if o.name.startswith('bld_'): bpy.data.objects.remove(o)
    (ob, tris), h, bw = place(kd, 0, 0, seed=1); ob.name = 'bld_' + kd
    # neighbours either side, the other types, so it reads as a street
    others = [k for k in TW.KINDS if k != kd]
    (o1, _), _, _ = place(others[0], -bw / 2 - 28, 0, seed=5); o1.name = 'bld_n1'
    (o2, _), _, _ = place(others[1], bw / 2 + 26, 0, seed=6); o2.name = 'bld_n2'
    d = max(h * 0.38, bw * 0.95)          # close in from the far pavement, at the corner, looking up the facade
    co.location = Vector((-bw * 0.85, -d - 10, 1.7)); co.rotation_euler = (Vector((-bw * 0.1, 6, h * 0.36)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, '%s.png' % kd); bpy.ops.render.render(write_still=True)
    stats[kd] = dict(tris=tris, height=round(h, 1)); print('TILE', kd, stats[kd])
json.dump(stats, open(os.path.join(OUT, 'stats.json'), 'w'))
