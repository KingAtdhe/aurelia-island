"""Quick look: render a .blend or .glb car from several views (Eevee, studio light). python3 look.py <file> <out_prefix> [views]"""
import sys, math, bpy
from mathutils import Vector
f, out = sys.argv[1], sys.argv[2]; views = sys.argv[3].split(',') if len(sys.argv) > 3 else ['q', 'side', 'front', 'rear', 'qr']
if f.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=f)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=f)
sc = bpy.context.scene
for m in bpy.data.materials:
    if m.name.startswith('Tyre'): m.diffuse_color = (0.03, 0.03, 0.032, 1)
for o in list(sc.objects):
    if o.type == 'MESH' and (o.name.endswith('_Far') or (o.parent and o.parent.name.startswith('LOD1'))): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = __import__('os').environ.get('CT', 'MATERIAL'); sh.show_specular_highlight = True; sh.show_shadows = False; sh.show_cavity = False; sc.display.render_aa = '8'
sc.render.resolution_x, sc.render.resolution_y = 1400, 800
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; sky = w.node_tree.nodes.new('ShaderNodeTexSky')
try: sky.sky_type = 'NISHITA'
except Exception: pass
w.node_tree.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.35
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(35)); sc.collection.objects.link(sun)
gm = bpy.data.meshes.new('g'); gm.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)]); g = bpy.data.objects.new('g', gm); sc.collection.objects.link(g)
gmat = bpy.data.materials.new('gm'); gmat.use_nodes = True; gmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.25, 0.26, 1); gm.materials.append(gmat)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
V = {'q': ((6.5, 4.8, 2.0), 50), 'side': ((0, 11, 1.0), 50), 'front': ((10, 0, 1.0), 50), 'rear': ((-10, 0, 1.0), 50), 'qr': ((-6.5, 4.8, 2.0), 50),
     'top': ((0.01, 0, 12), 40), 'wheel': ((1.8, 3.2, 0.6), 50), 'qn': ((4.2, 3.2, 1.4), 40)}
for v in views:
    p, lens = V[v]; cam.location = p; cam.data.lens = lens
    tgt = Vector((0, 0, 0.8)) if v not in ('wheel',) else Vector((1.3, 0.9, 0.4))
    if v == 'qn': tgt = Vector((1.8, 0.3, 0.8))
    d = tgt - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '%s_%s.png' % (out, v); bpy.ops.render.render(write_still=True)
