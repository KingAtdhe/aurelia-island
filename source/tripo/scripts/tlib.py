import bpy, bmesh, os, math, random
import numpy as np
from mathutils import Vector

TEX = '/home/claude/tripo/tex/'
IN = '/home/claude/tripo/in/'
OUT = '/home/claude/tripo/out/'
os.makedirs(OUT, exist_ok=True)


def load(fname, height=None, scale=None):
    """Import a Tripo FBX, apply transforms, set real size (metres), base at z=0, centred."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import tlib as _t
    bpy.ops.import_scene.fbx(filepath=_t.IN + fname + '.fbx')
    o = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    for x in list(bpy.data.objects):
        if x != o:
            bpy.data.objects.remove(x)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = o.data
    co = np.array([v.co[:] for v in me.vertices])
    mn, mx = co.min(0), co.max(0)
    s = scale if scale else height / (mx[2] - mn[2])
    c = np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])
    co = (co - c) * s
    me.vertices.foreach_set('co', co.ravel())
    # clean: remove zero-area faces, merge exact doubles, consistent outward normals
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bad = [f for f in bm.faces if f.calc_area() < 1e-9]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context='FACES')
    # keep Tripo's original winding: recalc flips open shells inward
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.clear()
    o.data.update()
    return o


def islands(o):
    """Return per-face island index and per-island (min,max) bbox."""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    fid = [-1] * len(bm.faces); boxes = []
    k = 0
    for f in bm.faces:
        if fid[f.index] >= 0:
            continue
        st = [f]; pts = []
        while st:
            g = st.pop()
            if fid[g.index] >= 0:
                continue
            fid[g.index] = k
            pts += [v.co.copy() for v in g.verts]
            for e in g.edges:
                for h in e.link_faces:
                    if fid[h.index] < 0:
                        st.append(h)
        a = np.array([p[:] for p in pts]); boxes.append((a.min(0), a.max(0)))
        k += 1
    bm.free()
    return fid, boxes


def face_attr(o, name, vals):
    me = o.data
    if name in me.attributes:
        me.attributes.remove(me.attributes[name])
    a = me.attributes.new(name, 'FLOAT', 'FACE')
    a.data.foreach_set('value', np.asarray(vals, dtype=np.float32))


# ---------- node helpers ----------
class M:
    def __init__(self, name):
        self.m = bpy.data.materials.new(name); self.m.use_nodes = True
        self.nt = self.m.node_tree; self.n = self.nt.nodes; self.l = self.nt.links
        self.bsdf = self.n['Principled BSDF']
        self.oc = self.n.new('ShaderNodeTexCoord').outputs['Object']
        self.geo = self.n.new('ShaderNodeNewGeometry')

    def tex(self, img, tile, offs=(0, 0, 0), blend=0.25, proj='BOX'):
        v = self.n.new('ShaderNodeVectorMath'); v.operation = 'MULTIPLY_ADD'
        v.inputs[1].default_value = (1 / tile[0], 1 / tile[1], 1 / tile[2]) if isinstance(tile, tuple) else (1 / tile,) * 3
        v.inputs[2].default_value = offs
        self.l.new(self.oc, v.inputs[0])
        t = self.n.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(TEX + img + '.png', check_existing=True)
        t.projection = proj; t.projection_blend = blend
        self.l.new(v.outputs[0], t.inputs[0])
        return t.outputs['Color']

    def math(self, op, a, b=None, clamp=False):
        m = self.n.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                self.l.new(x, m.inputs[i])
        return m.outputs[0]

    def ramp(self, x, lo, hi):
        r = self.n.new('ShaderNodeMapRange'); r.clamp = True
        self.l.new(x, r.inputs['Value']); r.inputs['From Min'].default_value = lo; r.inputs['From Max'].default_value = hi
        r.interpolation_type = 'SMOOTHSTEP'
        return r.outputs[0]

    def nz(self):
        s = self.n.new('ShaderNodeSeparateXYZ'); self.l.new(self.geo.outputs['Normal'], s.inputs[0]); return s.outputs['Z']

    def pz(self):
        s = self.n.new('ShaderNodeSeparateXYZ'); self.l.new(self.oc, s.inputs[0]); return s.outputs['Z']

    def attr(self, name):
        a = self.n.new('ShaderNodeAttribute'); a.attribute_type = 'GEOMETRY'; a.attribute_name = name; return a.outputs['Fac']

    def noise(self, scale, detail=4):
        t = self.n.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value = scale; t.inputs['Detail'].default_value = detail
        self.l.new(self.oc, t.inputs['Vector']); return t.outputs['Fac']

    def mix(self, fac, a, b):
        m = self.n.new('ShaderNodeMix'); m.data_type = 'RGBA'
        if isinstance(fac, (int, float)):
            m.inputs['Factor'].default_value = fac
        else:
            self.l.new(fac, m.inputs['Factor'])
        for sock, x in ((m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(x, tuple):
                sock.default_value = x + (1,) if len(x) == 3 else x
            else:
                self.l.new(x, sock)
        return m.outputs[2]

    def rgb(self, c):
        r = self.n.new('ShaderNodeRGB'); r.outputs[0].default_value = tuple(c) + (1,); return r.outputs[0]

    def tint(self, col, c, amt=1.0):
        m = self.n.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = 'MULTIPLY'
        m.inputs['Factor'].default_value = amt; self.l.new(col, m.inputs[6]); m.inputs[7].default_value = tuple(c) + (1,)
        return m.outputs[2]

    def hue(self, col, h=0.5, s=1.0, v=1.0):
        m = self.n.new('ShaderNodeHueSaturation'); self.l.new(col, m.inputs['Color'])
        m.inputs['Hue'].default_value = h; m.inputs['Saturation'].default_value = s; m.inputs['Value'].default_value = v
        return m.outputs[0]

    def out(self, col, rough=0.85, bump=0.35, metal=0.0):
        self.l.new(col, self.bsdf.inputs['Base Color'])
        self.bsdf.inputs['Roughness'].default_value = rough
        self.bsdf.inputs['Metallic'].default_value = metal
        if bump:
            g = self.n.new('ShaderNodeRGBToBW'); self.l.new(col, g.inputs[0])
            b = self.n.new('ShaderNodeBump'); b.inputs['Strength'].default_value = bump; b.inputs['Distance'].default_value = 0.02
            self.l.new(g.outputs[0], b.inputs['Height']); self.l.new(b.outputs[0], self.bsdf.inputs['Normal'])
        return self.m


def assign(o, mats, face_slot):
    me = o.data; me.materials.clear()
    for m in mats:
        me.materials.append(m.m if isinstance(m, M) else m)
    me.polygons.foreach_set('material_index', np.asarray(face_slot, dtype=np.int32))
    me.update()


def face_data(o):
    me = o.data; n = len(me.polygons)
    c = np.zeros(n * 3); nn = np.zeros(n * 3); ar = np.zeros(n)
    me.polygons.foreach_get('center', c); me.polygons.foreach_get('normal', nn); me.polygons.foreach_get('area', ar)
    return c.reshape(-1, 3), nn.reshape(-1, 3), ar


# ---------- bake ----------
def bake(o, name, res=1024, ao_samples=16, ao_dist=0.6, ao_strength=0.75, rough=0.85, alpha_from=None, margin_uv=0.012, lo_tris=None, extr=None):
    """Bake the procedurally textured high mesh onto a decimated low mesh (or itself if lo_tris is None)."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False
    hi = o
    tris = sum(len(p.vertices) - 2 for p in hi.data.polygons)
    co = np.array([v.co[:] for v in hi.data.vertices]); diag = float(np.linalg.norm(co.max(0) - co.min(0)))
    lo = hi.copy(); lo.data = hi.data.copy(); sc.collection.objects.link(lo); lo.name = name
    if lo_tris and tris > lo_tris:
        bpy.ops.object.select_all(action='DESELECT'); lo.select_set(True); bpy.context.view_layer.objects.active = lo
        m = lo.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = lo_tris / tris; m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='d')
    me = lo.data
    for u in list(me.uv_layers): me.uv_layers.remove(u)
    uv = me.uv_layers.new(name='bake'); me.uv_layers.active = uv
    bpy.ops.object.select_all(action='DESELECT'); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=margin_uv, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin_uv, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    imgs = {}
    for kind in ('col', 'ao', 'nrm'):
        im = bpy.data.images.new(f'{name}_{kind}', res, res, alpha=False, float_buffer=False)
        if kind == 'nrm': im.colorspace_settings.name = 'Non-Color'
        imgs[kind] = im
    # lo gets a bake-target material; hi keeps its procedural materials
    tm = bpy.data.materials.new('__t'); tm.use_nodes = True
    me.materials.clear(); me.materials.append(tm)
    me.polygons.foreach_set('material_index', np.zeros(len(me.polygons), dtype=np.int32)); me.update()
    tn = tm.node_tree.nodes.new('ShaderNodeTexImage'); tm.node_tree.nodes.active = tn
    bpy.ops.object.select_all(action='DESELECT'); hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    s2a = lo_tris is not None
    ex = extr if extr is not None else 0.02 * diag
    kw = dict(use_clear=True, margin=16, use_selected_to_active=s2a, cage_extrusion=ex, max_ray_distance=ex * 2.5)
    bk = sc.render.bake; bk.margin = 16
    sc.cycles.samples = 1
    tn.image = imgs['col']; bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, **kw)
    tn.image = imgs['nrm']; bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', **kw)
    sc.cycles.samples = ao_samples
    if not sc.world: sc.world = bpy.data.worlds.new('w')
    sc.world.light_settings.distance = ao_dist
    # AO from the high mesh onto the low one
    tn.image = imgs['ao']; bpy.ops.object.bake(type='AO', **kw)
    def arr(im): return np.array(im.pixels[:], dtype=np.float32).reshape(res, res, 4)
    col = arr(imgs['col']); ao = arr(imgs['ao'])[..., :1]
    col[..., :3] *= 1 - ao_strength * (1 - ao)
    from PIL import Image
    def save(a, p, q=90):
        Image.fromarray(np.clip(a[::-1] * 255 + 0.5, 0, 255).astype(np.uint8)).save(p, quality=q)
    save(col[..., :3], OUT + f'{name}_col.jpg'); save(arr(imgs['nrm'])[..., :3], OUT + f'{name}_nrm.jpg', 92); save(arr(imgs['ao'])[..., :3], OUT + f'{name}_ao.jpg')
    fm = bpy.data.materials.new(name); fm.use_nodes = True
    nd = fm.node_tree.nodes; ln = fm.node_tree.links; b = nd['Principled BSDF']
    ti = nd.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(OUT + f'{name}_col.jpg'); ln.new(ti.outputs[0], b.inputs['Base Color'])
    t2 = nd.new('ShaderNodeTexImage'); t2.image = bpy.data.images.load(OUT + f'{name}_nrm.jpg'); t2.image.colorspace_settings.name = 'Non-Color'
    nm = nd.new('ShaderNodeNormalMap'); ln.new(t2.outputs[0], nm.inputs['Color']); ln.new(nm.outputs[0], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough
    me.materials.clear(); me.materials.append(fm)
    for p in me.polygons: p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    bpy.ops.export_scene.gltf(filepath=OUT + name + '.glb', export_format='GLB', use_selection=True,
                              export_image_format='JPEG', export_jpeg_quality=88, export_apply=True,
                              export_attributes=False, export_normals=True, export_tangents=False)
    return fm
