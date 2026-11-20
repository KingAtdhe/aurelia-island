"""Render the presentation cameras stored in the .blend.  python3 render_map.py -- <blend> <outdir> [samples] [width] [cam name filter]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
blend, out = a[0], a[1]; samples = int(a[2]) if len(a) > 2 else 48; W = int(a[3]) if len(a) > 3 else 1600; flt = a[4] if len(a) > 4 else 'CAM_'; mode = a[5] if len(a) > 5 else 'day'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scn = bpy.data.scenes['Night'] if mode == 'night' else bpy.context.scene
if mode == 'night': bpy.context.window.scene = scn
if mode == 'clay':
    cm = bpy.data.materials.new('Clay'); cm.use_nodes = True; cm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.62, 0.62, 0.62, 1); scn.view_layers[0].material_override = cm
scn.cycles.samples = samples; scn.cycles.max_bounces = 4; scn.render.resolution_x = W; scn.render.resolution_y = int(W * 9 / 16)
scn.render.image_settings.file_format = 'JPEG'; scn.render.image_settings.quality = 90
if mode == 'day':                                                         # aerial perspective: distant surfaces fade toward a pale blue haze
    scn.view_layers[0].use_pass_mist = True; ms = scn.world.mist_settings; ms.start = 120; ms.depth = 4200; ms.falloff = 'QUADRATIC'
    ng = bpy.data.node_groups.new('Haze', 'CompositorNodeTree'); scn.compositing_node_group = ng; ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers'); mf = ng.nodes.new('ShaderNodeMath'); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = 0.5
    mx = ng.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0.58, 0.68, 0.82, 1); go_ = ng.nodes.new('NodeGroupOutput')
    ng.links.new(rl.outputs['Mist'], mf.inputs[0]); ng.links.new(mf.outputs[0], mx.inputs[0]); ng.links.new(rl.outputs['Image'], mx.inputs[6]); ng.links.new(mx.outputs[2], go_.inputs[0])
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type == 'CAMERA' and any(f in o.name for f in flt.split(',')):
        if mode == 'day': mf.inputs[1].default_value = 0.08 if 'Aerial' in o.name else 0.5      # the aerial view is 4 km out: keep its haze light
        scn.camera = o; scn.render.filepath = os.path.join(out, ('render_' if mode == 'day' else mode + '_') + o.name[4:] + '.jpg'); bpy.ops.render.render(write_still=True, scene=scn.name); print('rendered', o.name)
