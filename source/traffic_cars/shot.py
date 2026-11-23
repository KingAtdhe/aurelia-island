import bpy, math, sys
from mathutils import Vector
name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'/home/claude/tcars/out/{name}.glb')
for o in bpy.data.objects:
    if o.name.startswith('LOD1'): o.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
sc.render.resolution_x = 900; sc.render.resolution_y = 560; sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.8, 0.86, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sc.collection.objects.link(sun)
bpy.ops.mesh.primitive_plane_add(size=60); g = bpy.context.object; m = bpy.data.materials.new('g'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (0.25, 0.25, 0.26, 1); g.data.materials.append(m)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
for k, az in enumerate((-55, 125, 0)):
    a = math.radians(az); t = Vector((0, 0, 0.75))
    cam.location = t + Vector((math.cos(a) * 8, math.sin(a) * 8, 2.0)); cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'/tmp/tc_{name}_{k}.png'; bpy.ops.render.render(write_still=True)
