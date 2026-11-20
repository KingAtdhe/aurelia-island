"""Night set-up inside the Blender file: a second scene 'Night' sharing every object, with moonlight, street lamps and lit windows.
Materials read the custom property 'night' (0 in the day scene, 1 in the night scene) through a View Layer attribute node."""
import math, bpy
import numpy as np


def _night(nt):
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_type = 'VIEW_LAYER'; a.attribute_name = 'night'; return a.outputs['Fac']


def setup(C):
    day = bpy.context.scene; day['night'] = 0.0
    # window glass: emission from the atlas, scaled by 'night'
    g = bpy.data.materials['WindowGlass'].node_tree; b = g.nodes['Principled BSDF']; m = g.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'; m.inputs[1].default_value = 5.0
    g.links.new(_night(g), m.inputs[0]); g.links.new(m.outputs[0], b.inputs['Emission Strength'])
    # textured facades (towers and the far building version): a share of the bays lit, picked per bay and floor
    for name, share, glow in (('FacadeGlass', 0.2, 0.8), ('FacadeWindows', 0.3, 1.4)):
        nt = bpy.data.materials[name].node_tree; b = nt.nodes['Principled BSDF']; uv = nt.nodes.new('ShaderNodeUVMap')
        fl = nt.nodes.new('ShaderNodeVectorMath'); fl.operation = 'FLOOR'; nt.links.new(uv.outputs[0], fl.inputs[0])
        wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '2D'; nt.links.new(fl.outputs[0], wn.inputs['Vector'])
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = share; nt.links.new(wn.outputs['Value'], lt.inputs[0])
        fr = nt.nodes.new('ShaderNodeVectorMath'); fr.operation = 'FRACTION'; nt.links.new(uv.outputs[0], fr.inputs[0]); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(fr.outputs[0], sp.inputs[0])
        v0 = nt.nodes.new('ShaderNodeMath'); v0.operation = 'GREATER_THAN'; v0.inputs[1].default_value = 0.27; nt.links.new(sp.outputs['Y'], v0.inputs[0])
        v1 = nt.nodes.new('ShaderNodeMath'); v1.operation = 'LESS_THAN'; v1.inputs[1].default_value = 0.76 if name == 'FacadeWindows' else 0.97; nt.links.new(sp.outputs['Y'], v1.inputs[0])
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(lt.outputs[0], mm.inputs[0]); nt.links.new(v0.outputs[0], mm.inputs[1])
        m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; nt.links.new(mm.outputs[0], m2.inputs[0]); nt.links.new(v1.outputs[0], m2.inputs[1])
        m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(_night(nt), m3.inputs[1])
        m4 = nt.nodes.new('ShaderNodeMath'); m4.operation = 'MULTIPLY'; m4.inputs[1].default_value = glow; nt.links.new(m3.outputs[0], m4.inputs[0])
        b.inputs['Emission Color'].default_value = (1.0, 0.78, 0.48, 1); nt.links.new(m4.outputs[0], b.inputs['Emission Strength'])
    nt = bpy.data.materials['ShopSigns'].node_tree; b = nt.nodes['Principled BSDF']; tx = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(tx.outputs['Color'], b.inputs['Emission Color']); m = nt.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'; m.inputs[1].default_value = 1.2; nt.links.new(_night(nt), m.inputs[0]); nt.links.new(m.outputs[0], b.inputs['Emission Strength'])
    ns = bpy.data.scenes.new('Night'); ns['night'] = 1.0
    for c in day.collection.children:
        if c.name != '15_LIGHTING': ns.collection.children.link(c)
    lc = bpy.data.collections.new('20_NIGHT_LIGHTING'); ns.collection.children.link(lc)
    moon = bpy.data.lights.new('MOON', 'SUN'); moon.energy = 0.06; moon.color = (0.62, 0.74, 1.0); moon.angle = 0.02
    mo = bpy.data.objects.new('MOON', moon); lc.objects.link(mo); mo.rotation_euler = (math.radians(48), 0, math.radians(140))
    ld = bpy.data.lights.new('STREET_LAMP', 'POINT'); ld.energy = 2600; ld.color = (1.0, 0.80, 0.52); ld.shadow_soft_size = 0.22
    for k, q in enumerate(C.lamps):
        o = bpy.data.objects.new('LAMP_%04d' % k, ld); lc.objects.link(o); o.location = (q[0], -q[2], q[1] - 0.15)
    w = bpy.data.worlds.new('World_Night'); ns.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.012, 0.02, 0.045, 1); bg.inputs[1].default_value = 0.3
    ns.camera = day.camera; ns.render.engine = 'CYCLES'; ns.cycles.samples = day.cycles.samples; ns.cycles.use_denoising = True
    try: ns.view_settings.view_transform = day.view_settings.view_transform; ns.view_settings.look = day.view_settings.look; ns.view_settings.exposure = 1.6
    except Exception: pass
    import isle_lib as L; L.STATS['night_lamps'] = len(C.lamps)
