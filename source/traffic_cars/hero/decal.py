"""Decals for traffic-car liveries: a grid laid on the body surface (side projection), textured with an RGBA picture, alpha cut at 0.5
(glTF alphaMode MASK -> alpha scissor in Godot). Used by porto_parts.py and taxi_parts.py."""
import numpy as np, bpy, bmesh
from mathutils import Vector

def material(name, path, rough=0.3, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    img = bpy.data.images.load(path); img.pack(); tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img
    nt.links.new(tx.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    rd = nt.nodes.new('ShaderNodeMath'); rd.operation = 'ROUND'; nt.links.new(tx.outputs['Alpha'], rd.inputs[0]); nt.links.new(rd.outputs[0], b.inputs['Alpha'])
    if emit: nt.links.new(tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    try: m.surface_render_method = 'DITHERED'
    except Exception: pass
    m.diffuse_color = (1, 1, 1, 1); return m

def side_decal(name, mat, s0, s1, z0, z1, sd, surf_point, nrm, B, Bn, link, ns=48, nz=14, lift=0.0016, flipu=False):
    """Grid over s0..s1 x z0..z1 on the side sd (+1 left, -1 right); u runs along s (reversed when flipu), v up."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new(); S = np.linspace(s0, s1, ns); Z = np.linspace(z0, z1, nz); V = {}
    for i, s in enumerate(S):
        for j, z in enumerate(Z):
            p = surf_point('sz', s, z, sd)
            if p is None: continue
            n = nrm(p[None])[0]; V[i, j] = bm.verts.new(B(p + n * lift))
    for i in range(ns - 1):
        for j in range(nz - 1):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if not all(k in V for k in q): continue
            f = bm.faces.new([V[k] for k in q])
            for l, k in zip(f.loops, q):
                u = k[0] / (ns - 1); l[uv].uv = ((1 - u) if flipu else u, k[1] / (nz - 1))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); out = Vector((0, sd, 0))
        if f.normal.dot(out) < 0: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); link(o); return o
