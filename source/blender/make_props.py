"""python3 make_props.py -- out [names]  -> out/aurelia_props.glb, .blend and studio renders props_*.jpg"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; OUT = a[0]; names = a[1].split(',') if len(a) > 1 else None
bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene
import isle_lib as L
L.OUT = OUT
import isle_props as P
import isle_houses as HS; HS.register()
import isle_sheds as SH; SH.register()
import isle_life as LF; LF.register()
lib = P.build(names=names)
if os.environ.get('AO', '0') == '1': P.bake_ao([e['lod0'] for e in lib.values()], OUT)
for k, e in lib.items(): print('%-14s LOD0 %6d tris  LOD1 %6d tris' % (k, e['t0'], e['t1']))
for o in bpy.data.objects: o.select_set(o.name.startswith('PROP_'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'aurelia_props.glb'), export_format='GLB', use_selection=True, export_yup=True, export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, 'aurelia_props.blend')))
# studio layout: LOD0 in rows
order = list(lib); x = 0.0; row = []
groups = [['lamp', 'signal', 'power_pole', 'shelter', 'board_a'], ['sign_speed', 'sign_curve', 'sign_stop', 'sign_priority', 'sign_parking', 'reflector', 'bollard'], ['bench', 'bin', 'hydrant', 'jersey', 'fence']]
for o in bpy.data.objects:
    if o.name.endswith('_LOD1'): o.hide_render = True
me = bpy.data.meshes.new('floor'); me.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)]); fl = bpy.data.objects.new('floor', me); scn.collection.objects.link(fl)
fm = bpy.data.materials.new('fl'); fm.use_nodes = True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.3, 0.3, 0.31, 1); fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8; me.materials.append(fm)
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.72, 0.8, 0.92, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 3.8; sun.angle = math.radians(2); so = bpy.data.objects.new('s', sun); scn.collection.objects.link(so); so.rotation_euler = (math.radians(48), 0, math.radians(-35))
cam = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cam); scn.collection.objects.link(co); scn.camera = co
scn.render.engine = 'CYCLES'; scn.cycles.samples = int(os.environ.get('SAMPLES', 40)); scn.render.resolution_x = 1400; scn.render.resolution_y = 788; scn.render.image_settings.file_format = 'JPEG'
scn.view_settings.view_transform = 'AgX'
for gi, g in enumerate(groups):
    g = [n for n in g if n in lib]
    if not g: continue
    for o in bpy.data.objects:
        if o.name.startswith('PROP_') and o.name.endswith('_LOD0'): o.hide_render = True
    sp = {0: 4.2, 1: 1.6, 2: 2.6}[gi]; xs = 0
    for n in g:
        o = lib[n]['lod0']; o.hide_render = False; o.location = (0, xs, 0); o.rotation_euler = (0, 0, 0); xs += sp + (2.5 if n in ('shelter', 'board_a') else 0)
    mid = (xs - sp) / 2 + {0: 1.5, 1: 0, 2: 0.5}[gi]; hgt = {0: 4.0, 1: 1.6, 2: 0.55}[gi]; dist = {0: 30, 1: 13, 2: 11}[gi]
    co.location = (dist * 0.92, mid - dist * 0.42, hgt + dist * 0.12); cam.lens = 40
    co.rotation_euler = (Vector((0, mid, hgt)) - Vector(co.location)).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.abspath(os.path.join(OUT, 'props_%d.jpg' % gi)); bpy.ops.render.render(write_still=True)
# close-up contact sheet, one frame per prop
if os.environ.get('CLOSE', '1') == '1':
    scn.render.resolution_x = scn.render.resolution_y = 420; scn.cycles.samples = 20; tiles = []
    for n, e in lib.items():
        for o in bpy.data.objects:
            if o.name.startswith('PROP_'): o.hide_render = True
        o = e['lod0']; o.hide_render = False; o.location = (0, 0, 0)
        import numpy as np
        V = np.array([v.co[:] for v in o.data.vertices]); lo, hi = V.min(0), V.max(0); c = (lo + hi) / 2; r = np.linalg.norm(hi - lo) / 2
        d = r / math.tan(math.radians(17)) * 1.05; dirv = Vector((0.78, -0.55, 0.3)).normalized()
        co.location = Vector(c) + dirv * d; cam.lens = 55; co.rotation_euler = (Vector(c) - co.location).to_track_quat('-Z', 'Y').to_euler()
        f = os.path.abspath(os.path.join(OUT, 'pc_%s.jpg' % n)); scn.render.filepath = f; bpy.ops.render.render(write_still=True); tiles.append((n, f))
    from PIL import Image, ImageDraw
    cols = 6; rows = (len(tiles) + cols - 1) // cols; sheet = Image.new('RGB', (cols * 420, rows * 420), 'white'); dr = ImageDraw.Draw(sheet)
    for i, (n, f) in enumerate(tiles):
        sheet.paste(Image.open(f), ((i % cols) * 420, (i // cols) * 420)); dr.text(((i % cols) * 420 + 8, (i // cols) * 420 + 6), '%s  %d tris' % (n, lib[n]['t0']), fill='black')
    sheet.save(os.path.join(OUT, 'props_sheet.jpg'), quality=88)
