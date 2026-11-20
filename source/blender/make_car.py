"""python3 make_car.py -- out   -> out/car_aurelia.glb (+ .blend, preview render)"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isle_car as CAR
OUT = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene
root = CAR.build_blender()
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'); print('car triangles', tris)
for o in bpy.data.objects: o.select_set(o.name.startswith('Aurelia') or o.name.startswith('Wheel'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'car_aurelia.glb'), export_format='GLB', use_selection=True, export_yup=True, export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, 'car_aurelia.blend')))
me = bpy.data.meshes.new('floor'); me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)]); fl = bpy.data.objects.new('floor', me); scn.collection.objects.link(fl)
fm = bpy.data.materials.new('fl'); fm.use_nodes = True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.25, 0.26, 1); me.materials.append(fm)
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.7, 0.78, 0.9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.8
sun = bpy.data.lights.new('s', 'SUN'); sun.energy = 3.5; so = bpy.data.objects.new('s', sun); scn.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(30))
cam = bpy.data.cameras.new('c'); cam.lens = 50; co = bpy.data.objects.new('c', cam); scn.collection.objects.link(co); scn.camera = co
scn.render.engine = 'CYCLES'; scn.cycles.samples = 48; scn.render.resolution_x = 1000; scn.render.resolution_y = 560; scn.render.image_settings.file_format = 'JPEG'
for nm, pos in (('f34', (-5.2, -6.4, 2.0)), ('r34', (5.0, 6.2, 2.2)), ('side', (-8.5, 0.0, 1.1))):
    co.location = pos; co.rotation_euler = (Vector((0, 0, 0.55)) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler(); scn.render.filepath = os.path.abspath(os.path.join(OUT, 'car_%s.jpg' % nm)); bpy.ops.render.render(write_still=True)
