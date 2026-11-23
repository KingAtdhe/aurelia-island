"""Light far model of a hero car for race rivals seen from more than ~30 m: every mesh joined and decimated, materials kept.
usage: python3 make_far_lod.py in.glb out.glb target_tris"""
import sys, bpy
src, out, target = sys.argv[sys.argv.index('--') + 1:][:3] if '--' in sys.argv else sys.argv[1:4]
target = int(target)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
skip = ('engine', 'Engine', 'Hose', 'Radiator', 'Fluid', 'Suspension', 'Interior', 'Seat', 'Pedal', 'Belt', 'Dash')
for o in ms:
    if any(s in o.name for s in skip): bpy.data.objects.remove(o)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects: o.select_set(o in ms)
bpy.context.view_layer.objects.active = ms[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')          # keep each part where the parent nodes put it (the Calder's root is turned)
bpy.ops.object.make_single_user(object=True, obdata=True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join(); ob = bpy.context.view_layer.objects.active; ob.name = 'Far'
for o in list(bpy.context.scene.objects):
    if o != ob: bpy.data.objects.remove(o)
ob.parent = None
tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0005); bpy.ops.object.mode_set(mode='OBJECT')
d = ob.modifiers.new('d', 'DECIMATE'); d.ratio = min(1.0, target / tris); d.use_collapse_triangulate = True; bpy.ops.object.modifier_apply(modifier='d')
for p in ob.data.polygons: p.use_smooth = True
print('far', src, tris, '->', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'mats', len(ob.data.materials))
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True, export_yup=True, export_image_format='NONE')   # textures come from the near model's materials at runtime
