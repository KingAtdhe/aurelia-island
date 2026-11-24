# Cycles top-down light bake of the whole island: sun visibility (R) and sky occlusion (G) for the terrain and road shaders.
# Renders one tile of a TX x TZ grid per run (TILE=i,j) so a crash or time limit loses little; combine_island.py joins them.
import bpy, json, math, os, sys, re, numpy as np, mathutils
X0, X1, Z0, Z1 = -2400.0, 2400.0, -1680.0, 1680.0
TX, TZ = int(os.environ.get('BTX', '4')), int(os.environ.get('BTZ', '3')); RES = int(os.environ.get('RES', '1536')); SPP = int(os.environ.get('SPP', '16'))
TI, TJ = (int(v) for v in os.environ['TILE'].split(','))
A = '/home/claude/aurelia-island/godot/assets/island/'; OUT = os.environ.get('OUT', '/home/claude/bake_isl/')
os.makedirs(OUT, exist_ok=True)
W, D = (X1 - X0) / TX, (Z1 - Z0) / TZ; tx0 = X0 + TI * W; tz0 = Z0 + TJ * D; M = 60.0      # tile with a margin so shadows from outside fall in
bpy.ops.wm.read_factory_settings(use_empty=True)
idx = json.load(open(A + 'index.json'))['chunks']
for nm, c in idx.items():
    if c['max'][0] < tx0 - M - 80 or c['min'][0] > tx0 + W + M + 80 or c['max'][2] < tz0 - M - 80 or c['min'][2] > tz0 + D + M + 80: continue
    bpy.ops.import_scene.gltf(filepath=A + 'chunks/%s.glb' % nm)
DARK = ('Houses', 'Structures', 'Props', 'Shapes', 'ArchTrim', 'KitTrim', 'Landmark', 'BuildingsHD', 'BuildingsLOD', 'Buildings', 'TowerCrown', 'Towers', 'Roofs', 'Glazing', 'Spin_', 'Rocks', 'TunnelPortal', 'Touge')          # bridges stay visible: their decks are driven on
for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    if any(o.name.startswith(p) for p in ('Water', 'Lake', 'River', 'Shallows', 'ShoreFoam', 'Seabed', 'Puddles', 'Skids', 'Markings', 'RoadDecals', 'ContactAO', 'TreeCards', 'TerrainBlend', 'Waterfall', 'Kerbs')):
        bpy.data.objects.remove(o); continue
    if any(o.name.startswith(p) for p in DARK): o.visible_camera = False          # casts shadow, not baked itself
# plants and props, instanced at their game positions
fd = json.load(open(A + 'flora.json')); fb = np.fromfile(A + 'flora.bin', '<f4')
coll = {}
for f in ('flora_flora', 'flora_kit', 'flora_tprops'):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=A + f + '.glb'); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        m = re.match(r'^S_(.+)_LOD0$', o.name)
        if not m: continue
        c = bpy.data.collections.new('L_' + m.group(1))
        def grab(x):
            for cc in list(x.users_collection): cc.objects.unlink(x)
            c.objects.link(x)
            for ch in x.children: grab(ch)
        mw = o.matrix_world.copy(); grab(o); o.matrix_world = mw; coll[m.group(1)] = c
    for o in new:
        if o.name in bpy.data.objects and not any(o.name in c.objects for c in coll.values()): bpy.data.objects.remove(o)
n = 0
for sp, (off, cnt) in fd['species'].items():
    if sp.startswith(('grass', 'flowers', 'prop_tcar', 'prop_reflector', 'prop_rk_post', 'prop_rk_cone', 'prop_cones')): continue
    src = fd['model'][sp]
    if src not in coll: continue
    a = fb[off:off + cnt * 8].reshape(-1, 8)
    for x, y, z, s, ya in a[:, :5]:
        if x < tx0 - M or x > tx0 + W + M or z < tz0 - M or z > tz0 + D + M: continue
        e = bpy.data.objects.new('i', None); e.instance_type = 'COLLECTION'; e.instance_collection = coll[src]
        e.location = (float(x), -float(z), float(y)); e.rotation_euler = (0, 0, float(ya)); e.scale = (float(s),) * 3
        e.visible_camera = False; bpy.context.scene.collection.objects.link(e); n += 1
print('instances', n)
for m in bpy.data.materials:                       # every surface plain white, keeping the cut-out alpha of leaves
    if not m.use_nodes: continue
    b = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if not b: continue
    for l in list(b.inputs['Base Color'].links): m.node_tree.links.remove(l)
    b.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
    if 'Emission Color' in b.inputs:
        for l in list(b.inputs['Emission Color'].links): m.node_tree.links.remove(l)
        b.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    for l in list(b.inputs['Normal'].links): m.node_tree.links.remove(l)
    b.inputs['Metallic'].default_value = 0; b.inputs['Roughness'].default_value = 1
    if 'Specular IOR Level' in b.inputs: b.inputs['Specular IOR Level'].default_value = 0
for im in list(bpy.data.images):                   # only leaf cut-outs need their pictures
    if not im.users: bpy.data.images.remove(im)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 1; sc.cycles.diffuse_bounces = 1; sc.cycles.transparent_max_bounces = 6
sc.render.resolution_x = RES; sc.render.resolution_y = int(round(RES * D / W)); sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = W; cam.data.clip_end = 3000; cam.location = (tx0 + W / 2, -(tz0 + D / 2), 900)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; bg = world.node_tree.nodes['Background']
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
d_g = mathutils.Euler((math.radians(-38), math.radians(-35), 0), 'ZXY').to_matrix() @ mathutils.Vector((0, 0, -1))
d_b = mathutils.Vector((d_g.x, -d_g.z, d_g.y)); sun.rotation_euler = d_b.to_track_quat('-Z', 'Y').to_euler(); sun.data.angle = math.radians(1.5)
def render(name, sun_e, sky_e, shadows=True):
    sun.data.energy = sun_e; sun.data.use_shadow = shadows; bg.inputs[1].default_value = sky_e; bg.inputs[0].default_value = (1, 1, 1, 1); sun.hide_render = sun_e == 0
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'; sc.render.filepath = OUT + '%s_%d_%d.exr' % (name, TI, TJ)
    bpy.ops.render.render(write_still=True)
for nm, a, b, s in (('sun', 3.0, 0.0, True), ('sunfree', 3.0, 0.0, False), ('sky', 0.0, 1.0, True)):
    if os.environ.get('ONLY') and nm not in os.environ['ONLY']: continue
    render(nm, a, b, s)
