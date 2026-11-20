"""Concept lineup of street furniture: props stood on a pavement at golden hour, rendered in Cycles.
python3 props_lineup.py -- OUTDIR samples width names(comma) [tag]"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; SAMP = int(a[1]); WID = int(a[2]); NAMES = a[3].split(','); TAG = a[4] if len(a) > 4 else 'lineup'
bpy.ops.wm.read_factory_settings(use_empty=True)
import isle_lib as L; L.OUT = OUT; os.makedirs(OUT, exist_ok=True)
import isle_props as P, isle_life as LF, isle_hero as H
from mathutils import Vector
LF.register(); import isle_houses as _HS, isle_sheds as _SH; _HS.register(); _SH.register()
try:
    import isle_props_hq as HQ; HQ.register()
except Exception as e: print('no hq', e)
M = H.hero_materials(P.materials()); scn = bpy.context.scene
lib = P.build(M, NAMES)
x = 0.0; pos = []
for n in NAMES:
    e = lib[n]; ob = e['lod0']; e['lod1'].hide_render = True
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]; w = max(v.x for v in bb) - min(v.x for v in bb); d = max(v.y for v in bb) - min(v.y for v in bb)
    sz = max(w, d, 0.8); ob.location = (x + sz / 2 - (min(v.x for v in bb) + max(v.x for v in bb)) / 2, -(min(v.y for v in bb) + max(v.y for v in bb)) / 2, 0.15)
    pos.append((n, x + sz / 2, sz, max(v.z for v in bb))); x += sz + 1.2
pave = L.new_mat('Pave', 0.8, image=L.make_image('pave_ph', np.clip(__import__('isle_photo').colour('PavingStones070', 0.62, 0.6), 0, 1)), vcol=True)
K = P.Part(); K.obj(P.bbox(x / 2, 0, 0.075, x + 30, 8, 0.15), pave, (0.9, 0.88, 0.84), 'box', 2.5); P.make_prop('Pave', K.arrays())
K = P.Part(); K.obj(P.bbox(x / 2, -4.1, 0.08, x + 30, 0.2, 0.16), M['stone'], (0.85, 0.84, 0.8)); K.obj(P.bbox(x / 2, -9, -0.02, x + 30, 10, 0.04), M['concrete'], (0.25, 0.25, 0.26)); P.make_prop('Kerb', K.arrays())
K = P.Part(); K.obj(P.bbox(x / 2, 6, 6, x + 30, 0.4, 12), M['brick2'], (1, 1, 1), 'box', 2.0); P.make_prop('Backwall', K.arrays())
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
sk = nt.nodes.new('ShaderNodeTexSky'); nt.links.new(sk.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.35; sk.sun_elevation = math.radians(20); sk.sun_rotation = math.radians(200)
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.color = (1.0, 0.84, 0.66); sun.angle = math.radians(1.5); so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so); so.rotation_euler = (math.radians(68), 0, math.radians(-40))
scn.render.engine = 'CYCLES'; scn.cycles.samples = SAMP; scn.cycles.use_denoising = True; scn.view_settings.view_transform = 'AgX'
cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); scn.collection.objects.link(co); scn.camera = co; cam.lens = 55
scn.render.resolution_x = WID; scn.render.resolution_y = WID; scn.view_settings.exposure = -0.6
sun.energy = 3.2; bg.inputs['Strength'].default_value = 0.22
obs = {n: lib[n]['lod0'] for n in NAMES}
for n, cx, sz, h in pos:
    for m, o in obs.items(): o.hide_render = (m != n)
    s = max(sz, h * 0.9, 1.2); tgt = Vector((cx, 0, h * 0.45)); d = s * 1.85 + 1.5
    co.location = tgt + Vector((d * 0.62, -d * 0.78, d * 0.32)); co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, '%s_%s.png' % (TAG, n)); bpy.ops.render.render(write_still=True)
import json; json.dump({'pos': pos}, open(os.path.join(OUT, TAG + '.json'), 'w'))
print('DONE', len(pos))
