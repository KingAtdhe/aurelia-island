# Cycles top-down light bake of the coast slice: sun visibility and sky occlusion -> bake_coast.png (R = sun, G = sky)
import bpy, json, math, sys, numpy as np, os
X0, X1, Z0, Z1 = -1950.0, -650.0, 280.0, 1340.0
RES = int(os.environ.get('RES', '2048')); SPP = int(os.environ.get('SPP', '24'))
OUT = '/home/claude/bake/'
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in ['/home/claude/gd_src/coast_base.glb', '/home/claude/gd_src/coast_detail.glb']:
    bpy.ops.import_scene.gltf(filepath=f)
# map pieces that do not block light
for o in list(bpy.data.objects):
    if o.type == 'MESH' and any(o.name.startswith(p) for p in ('Houses', 'Structures', 'Props', 'Shapes', 'ArchTrim', 'KitTrim', 'Landmark')): o.visible_camera = False
for o in list(bpy.data.objects):
    if o.type == 'MESH' and any(o.name.startswith(p) for p in ('Water', 'Shallows', 'ShoreFoam', 'Seabed', 'Puddles', 'Skids', 'Markings', 'RoadDecals', 'ContactAO', 'TreeCards', 'TerrainBlend')):
        bpy.data.objects.remove(o)
# plants and props from the flora library, instanced at their game positions
lib_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath='/home/claude/aurelia-island/godot/assets/flora_coast.glb')
lib_objs = [o for o in bpy.data.objects if o not in lib_before]
TT = {'pine': 'tree_t_pine', 'oak': 'tree_t_oak', 'oak_b': 'tree_t_oak', 'fruit': 'tree_t_olive', 'cypress': 'tree_t_cypress'}
coll = {}
for o in lib_objs:
    if o.name.startswith('S_') and o.name.endswith('_LOD0'):
        sp = o.name[2:-5]; c = bpy.data.collections.new('L_' + sp)
        def grab(x):
            for cc in x.users_collection: cc.objects.unlink(x)
            c.objects.link(x)
            for ch in x.children: grab(ch)
        mw = o.matrix_world.copy(); grab(o); o.matrix_world = mw
        coll[sp] = c
for o in lib_objs:
    if o.name in bpy.data.objects and not any(o.name in c.objects for c in coll.values()):
        bpy.data.objects.remove(o)
data = json.load(open('/home/claude/aurelia-island/godot/assets/coast_flora.json'))
n = 0
for sp, a in data.items():
    if sp.startswith(('grass', 'flowers', 'prop_tcar', 'prop_reflector', 'prop_rk_post')): continue
    src = TT.get(sp, sp)
    if src not in coll: continue
    for i in range(0, len(a), 8):
        x, y, z, s, yaw = a[i:i + 5]
        e = bpy.data.objects.new('i', None); e.instance_type = 'COLLECTION'; e.instance_collection = coll[src]
        e.location = (x, -z, y); e.rotation_euler = (0, 0, yaw); e.scale = (s, s, s)
        e.visible_camera = False; bpy.context.scene.collection.objects.link(e); n += 1
print('instances', n)
# every surface white, keeping cut-out alpha of leaves
for m in bpy.data.materials:
    if not m.use_nodes: continue
    b = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if not b: continue
    for l in list(b.inputs['Base Color'].links): m.node_tree.links.remove(l)
    b.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
    for nm in ('Emission Color',):
        if nm in b.inputs:
            for l in list(b.inputs[nm].links): m.node_tree.links.remove(l)
            b.inputs[nm].default_value = (0, 0, 0, 1)
    b.inputs['Metallic'].default_value = 0; b.inputs['Roughness'].default_value = 1
    if 'Specular IOR Level' in b.inputs: b.inputs['Specular IOR Level'].default_value = 0
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 1; sc.cycles.diffuse_bounces = 1; sc.cycles.transparent_max_bounces = 8
W, D = X1 - X0, Z1 - Z0
sc.render.resolution_x = RES; sc.render.resolution_y = int(RES * D / W); sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = W; cam.data.clip_end = 2000
cam.location = ((X0 + X1) / 2, -(Z0 + Z1) / 2, 600); cam.rotation_euler = (0, 0, 0)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; bg = world.node_tree.nodes['Background']
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
# Godot sun: rotation_degrees (-38, -35, 0) -> direction the light travels; Blender sun points along its local -Z
import mathutils
d_g = mathutils.Euler((math.radians(-38), math.radians(-35), 0), 'ZXY').to_matrix() @ mathutils.Vector((0, 0, -1))   # Godot: Y up, light shines along -Z
d_b = mathutils.Vector((d_g.x, -d_g.z, d_g.y))                                                                          # to Blender (Z up, y = -game z)
sun.rotation_euler = d_b.to_track_quat('-Z', 'Y').to_euler(); sun.data.angle = math.radians(1.5)
print('sun dir (blender)', tuple(round(v, 3) for v in d_b))
def render(name, sun_e, sky_e, shadows=True):
    sun.data.energy = sun_e; sun.data.use_shadow = shadows; bg.inputs[1].default_value = sky_e; bg.inputs[0].default_value = (1, 1, 1, 1)
    sun.hide_render = sun_e == 0
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.filepath = OUT + name + '.exr'
    bpy.ops.render.render(write_still=True)
render('sun', 3.0, 0.0, True)
render('sunfree', 3.0, 0.0, False)
render('sky', 0.0, 1.0)
