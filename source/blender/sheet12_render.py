"""Art sheet 12 tiles: each traffic car on asphalt in soft evening light, front three-quarter (and rear three-quarter variants).
python3 sheet12_render.py -- OUTDIR samples size kinds  (kinds comma list; 'kind@rear' for the rear view, 'kind@clay' for clay)"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh, numpy as np
from mathutils import Vector
import isle_traffic_hq as TH
import isle_photo as PH, isle_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]; OUT, SPP, SIZE, NAMES = argv[0], int(argv[1]), int(argv[2]), argv[3].split(',')
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene
scn.render.engine = 'CYCLES'; scn.cycles.samples = SPP; scn.cycles.use_denoising = True; scn.render.resolution_x = scn.render.resolution_y = SIZE
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'; scn.view_settings.exposure = -0.2
PAINTS = {'hatch': (0.62, 0.03, 0.03), 'sedan': (0.05, 0.12, 0.32), 'estate': (0.62, 0.62, 0.6), 'suv': (0.12, 0.2, 0.14), 'van': (0.9, 0.9, 0.88), 'pickup': (0.55, 0.32, 0.08), 'taxi': (0.95, 0.68, 0.05)}
def mat(name, col, rough, metal=0.0, coat=0.0, em=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.03
    if em: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = em
    if alpha < 1: b.inputs['Alpha'].default_value = alpha
    return m
CLAY = mat('clay', (0.7, 0.7, 0.7), 0.6)
Z = {TH.GLASS: mat('glass', (0.01, 0.015, 0.02), 0.02, 0.0, 0.0), TH.BLACK: mat('black', (0.025, 0.025, 0.027), 0.45), TH.CHROME: mat('chrome', (0.9, 0.9, 0.92), 0.08, 1.0),
     TH.LAMP_F: mat('lampf', (0.95, 0.96, 1.0), 0.05, 0, 0, 2.0), TH.LAMP_R: mat('lampr', (0.75, 0.02, 0.01), 0.1, 0, 0, 1.5), TH.TYRE: mat('tyre', (0.02, 0.02, 0.022), 0.85),
     TH.RIM: mat('rim', (0.7, 0.71, 0.74), 0.22, 1.0), TH.PLATE: mat('plate', (0.92, 0.92, 0.88), 0.4), TH.AMBER: mat('amber', (1.0, 0.55, 0.05), 0.1, 0, 0, 1.2),
     TH.CLAD: mat('clad', (0.05, 0.05, 0.055), 0.7), TH.DISC: mat('disc', (0.3, 0.29, 0.28), 0.4, 0.8)}
# ground: photo asphalt with a painted lane edge, sky: warm low sun
g = PH.colour('Asphalt010', 0.32, 0.25) if hasattr(PH, 'colour') else None
gm = L.new_mat('Ground', 0.82, image=L.make_image('asph', np.clip(g, 0, 1))) if g is not None else mat('ground', (0.12, 0.12, 0.12), 0.8)
nt = gm.node_tree; tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.3, 0.3, 0.3)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); [nt.links.new(mp.outputs['Vector'], n.inputs['Vector']) for n in nt.nodes if n.type == 'TEX_IMAGE']
me = bpy.data.meshes.new('g'); me.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)]); go = bpy.data.objects.new('g', me); scn.collection.objects.link(go); me.materials.append(gm)
lm = bpy.data.meshes.new('l'); lm.from_pydata([(-60, -2.6, 0.003), (60, -2.6, 0.003), (60, -2.45, 0.003), (-60, -2.45, 0.003)], [], [(0, 1, 2, 3)]); lo = bpy.data.objects.new('l', lm); scn.collection.objects.link(lo); lm.materials.append(mat('line', (0.85, 0.85, 0.82), 0.6))
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; wn = w.node_tree; sk = wn.nodes.new('ShaderNodeTexSky')
try: sk.sky_type = 'NISHITA'; sk.sun_elevation = math.radians(14); sk.sun_rotation = math.radians(210); sk.air_density = 1.4; sk.dust_density = 2.0
except Exception: pass
wn.links.new(sk.outputs['Color'], wn.nodes['Background'].inputs['Color']); wn.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.2; sun.color = (1.0, 0.82, 0.62); sun.angle = math.radians(2.0); so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
so.rotation_euler = (math.radians(76), 0, math.radians(210 - 90))
fill = bpy.data.lights.new('fill', 'AREA'); fill.energy = 900; fill.size = 8; fo = bpy.data.objects.new('fill', fill); fo.location = (6, -8, 6); fo.rotation_euler = (math.radians(55), 0, math.radians(38)); scn.collection.objects.link(fo)
cam = bpy.data.cameras.new('c'); cam.lens = 55; co = bpy.data.objects.new('c', cam); scn.collection.objects.link(co); scn.camera = co
stats = {}
for nm in NAMES:
    kind, _, view = nm.partition('@')
    for o in [o for o in scn.objects if o.name.startswith('car_')]: bpy.data.objects.remove(o, do_unlink=True)
    paint = mat('paint_' + kind, PAINTS[kind], 0.18, 0.35 if kind not in ('van', 'taxi') else 0.0, 1.0)
    parts = TH.build(kind, 0); tri = 0
    for k, (bm, zone) in enumerate(parts):
        bmesh.ops.triangulate(bm, faces=bm.faces[:]); tri += len(bm.faces)
        m_ = bpy.data.meshes.new('car_%d' % k); bm.to_mesh(m_); bm.free(); o = bpy.data.objects.new('car_%d' % k, m_); scn.collection.objects.link(o)
        m_.materials.append(CLAY if view == 'clay' else (paint if zone == TH.PAINT else Z[zone]))
        for p in m_.polygons: p.use_smooth = zone in (TH.PAINT, TH.GLASS, TH.TYRE, TH.RIM, TH.CLAD, TH.CHROME)
    sp = TH.TYPES[kind]; hl = sp['L'] / 2; tgt = Vector((0.0, 0.0, 0.62))
    d = sp['L'] * 1.55; az = math.radians(-38 if view != 'rear' else -142); el = math.radians(9)
    co.location = tgt + Vector((d * math.cos(el) * math.cos(az), d * math.cos(el) * math.sin(az), d * math.sin(el))); co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, nm.replace('@', '_') + '.png'); bpy.ops.render.render(write_still=True)
    stats[nm.replace('@', '_')] = dict(tris=tri, height=round(float(max(TH.stations(sp)[4])), 2)); print('TILE', nm, stats[nm.replace('@', '_')])
json.dump(stats, open(os.path.join(OUT, 'stats.json'), 'w'))
