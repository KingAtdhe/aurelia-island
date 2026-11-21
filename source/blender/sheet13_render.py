"""Concept 13 tiles: ground, verges and grass, rendered in Cycles at game-camera height.
python3 sheet13_render.py -- OUTDIR name samples width height
Ground is displaced photo-scanned CC0 material (ambientCG, decoded to PHOTO as raw RGBA 512); grass is modelled blade by blade."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; OUT, NAME, SAMP, W, H = a[0], a[1], int(a[2]), int(a[3]), int(a[4])
PHOTO = os.environ.get('PHOTO', '/home/claude/photo13'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(13)

bpy.ops.wm.read_factory_settings(use_empty=True); scn = bpy.context.scene

# ------------------------------------------------------------------ textures and materials
_IM = {}
def img(set_, kind):
    k = set_ + '_' + kind
    if k in _IM: return _IM[k]
    f = os.path.join(PHOTO, k + '.raw')
    if not os.path.exists(f): return None
    from PIL import Image as _PI
    png = '/tmp/s13tex/%s.png' % k; os.makedirs('/tmp/s13tex', exist_ok=True)
    if not os.path.exists(png): _PI.fromarray(np.fromfile(f, np.uint8).reshape(512, 512, 4)[..., :3]).save(png)
    im = bpy.data.images.load(png)
    if kind != 'Color': im.colorspace_settings.name = 'Non-Color'
    _IM[k] = im; return im

def pbr(name, set_, scale=1.0, tint=(1, 1, 1), box=False, nstr=1.0, rough_add=0.3, moss=None, moss_amt=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links.new
    b = N['Principled BSDF']; tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3
    Lk(tc.outputs['Object' if box else 'UV'], mp.inputs['Vector'])
    def tex(kind):
        im = img(set_, kind)
        if im is None: return None
        t = N.new('ShaderNodeTexImage'); t.image = im
        if box: t.projection = 'BOX'; t.projection_blend = 0.25
        Lk(mp.outputs['Vector'], t.inputs['Vector']); return t
    c = tex('Color'); ao = tex('AmbientOcclusion'); r = tex('Roughness'); n = tex('NormalGL')
    col = c.outputs['Color']
    mt = N.new('ShaderNodeMix'); mt.data_type = 'RGBA'; mt.blend_type = 'MULTIPLY'; mt.inputs[0].default_value = 1.0; mt.inputs[7].default_value = (*tint, 1)
    Lk(col, mt.inputs[6]); col = mt.outputs[2]
    if ao:
        ma = N.new('ShaderNodeMix'); ma.data_type = 'RGBA'; ma.blend_type = 'MULTIPLY'; ma.inputs[0].default_value = 0.8; Lk(col, ma.inputs[6]); Lk(ao.outputs['Color'], ma.inputs[7]); col = ma.outputs[2]
    if moss:                                   # moss on the faces that look up
        mc = bpy.data.images.get(moss + '_Color') or img(moss, 'Color'); t2 = N.new('ShaderNodeTexImage'); t2.image = mc; t2.projection = 'BOX'; t2.projection_blend = 0.3; Lk(mp.outputs['Vector'], t2.inputs['Vector'])
        geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Normal'], sep.inputs[0])
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; Lk(tc.outputs['Object'], nz.inputs['Vector'])
        ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; Lk(sep.outputs['Z'], ad.inputs[0]); Lk(nz.outputs['Fac'], ad.inputs[1])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.15 - moss_amt; mr.inputs['From Max'].default_value = 1.35 - moss_amt; Lk(ad.outputs[0], mr.inputs['Value'])
        mm = N.new('ShaderNodeMix'); mm.data_type = 'RGBA'; Lk(mr.outputs['Result'], mm.inputs[0]); Lk(col, mm.inputs[6]); Lk(t2.outputs['Color'], mm.inputs[7]); col = mm.outputs[2]
    Lk(col, b.inputs['Base Color'])
    if r:
        rr = N.new('ShaderNodeMath'); rr.operation = 'ADD'; rr.inputs[1].default_value = rough_add; rr.use_clamp = True; Lk(r.outputs['Color'], rr.inputs[0]); Lk(rr.outputs[0], b.inputs['Roughness'])
    else: b.inputs['Roughness'].default_value = 0.85
    if n:
        nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr; Lk(n.outputs['Color'], nm.inputs['Color']); Lk(nm.outputs['Normal'], b.inputs['Normal'])
    try: b.inputs['Specular IOR Level'].default_value = 0.0 if not box else 0.3
    except Exception: pass
    return m

def blade_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links.new; b = N['Principled BSDF']; out = N['Material Output']
    at = N.new('ShaderNodeVertexColor'); at.layer_name = 'Col'; Lk(at.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.55
    try: b.inputs['Specular IOR Level'].default_value = 0.3
    except Exception: pass
    tl = N.new('ShaderNodeBsdfTranslucent'); hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 1.4; hs.inputs['Saturation'].default_value = 1.2
    Lk(at.outputs['Color'], hs.inputs['Color']); Lk(hs.outputs[0], tl.inputs['Color'])
    mx = N.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.32; Lk(b.outputs[0], mx.inputs[1]); Lk(tl.outputs[0], mx.inputs[2]); Lk(mx.outputs[0], out.inputs['Surface'])
    return m

def plain(name, col, rough=0.6, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    try: b.inputs['Specular IOR Level'].default_value = spec
    except Exception: pass
    return m

# ------------------------------------------------------------------ geometry helpers
def mesh_obj(name, V, F, mat=None, cols=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(np.asarray(V).tolist(), [], np.asarray(F).tolist()); me.update()
    if cols is not None:
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT'); ca.data.foreach_set('color', np.c_[cols, np.ones(len(cols))].astype(np.float32).ravel())
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); scn.collection.objects.link(ob)
    if mat: me.materials.append(mat)
    return ob

def ground(name, mat, sx, sy, res, disp_set=None, disp=0.0, shape=None):
    """Grid of sx x sy metres, res cells per metre; height = photo displacement * disp + shape(x, y)."""
    nx, ny = max(1, int(sx * res)), max(1, int(sy * res)); xs = np.linspace(-sx / 2, sx / 2, nx + 1); ys = np.linspace(-sy / 2, sy / 2, ny + 1)
    X, Y = np.meshgrid(xs, ys, indexing='xy'); Z = np.zeros_like(X); U = (X + sx / 2) / 1.0; Vv = (Y + sy / 2) / 1.0
    if disp_set and disp and os.path.exists(os.path.join(PHOTO, disp_set + '_Displacement.raw')):
        hm = np.fromfile(os.path.join(PHOTO, disp_set + '_Displacement.raw'), np.uint8).reshape(512, 512, 4)[..., 0].astype(np.float32) / 255.0
        sc = mat_scale.get(name, 1.0); iu = ((U * sc) % 1.0 * 511).astype(int); iv = ((1 - (Vv * sc) % 1.0) * 511).astype(int); Z += (hm[iv, iu] - 0.5) * disp
    if shape: Z += shape(X, Y)
    V = np.c_[X.ravel(), Y.ravel(), Z.ravel()]; idx = np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1)
    F = np.c_[idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()]
    ob = mesh_obj(name, V, F, mat); me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    uv = np.c_[U.ravel(), Vv.ravel()]; li = np.array([l.vertex_index for l in me.loops]); uvl.data.foreach_set('uv', uv[li].ravel().astype(np.float32))
    return ob
mat_scale = {}

def surface(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); me = e.to_mesh()
    bvh = BVHTree.FromPolygons([ob.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return bvh
def drop(bvh, x, y):
    h = bvh.ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)))
    return h[0].z if h[0] is not None else 0.0

STYLE = {   # blade height range, width, lean, root colour, tip colour, blades per clump
    'lush': dict(h=(0.07, 0.24), w=0.005, lean=0.4, root=(0.03, 0.06, 0.012), tip=(0.17, 0.30, 0.055), dry=(0.40, 0.40, 0.14), dryf=0.15, n=(10, 22)),
    'dry': dict(h=(0.10, 0.32), w=0.0045, lean=0.45, root=(0.09, 0.09, 0.03), tip=(0.55, 0.47, 0.20), dry=(0.32, 0.36, 0.11), dryf=0.35, n=(10, 22)),
    'verge': dict(h=(0.06, 0.26), w=0.0055, lean=0.4, root=(0.04, 0.07, 0.015), tip=(0.24, 0.33, 0.08), dry=(0.48, 0.42, 0.18), dryf=0.3, n=(10, 22)),
    'dune': dict(h=(0.35, 0.80), w=0.0040, lean=0.55, root=(0.10, 0.12, 0.07), tip=(0.42, 0.48, 0.34), dry=(0.62, 0.55, 0.36), dryf=0.4, n=(14, 30)),
    'short': dict(h=(0.03, 0.10), w=0.0045, lean=0.5, root=(0.03, 0.055, 0.012), tip=(0.14, 0.24, 0.05), dry=(0.34, 0.33, 0.12), dryf=0.2, n=(16, 30)),
    'shortdry': dict(h=(0.04, 0.12), w=0.004, lean=0.5, root=(0.08, 0.08, 0.03), tip=(0.42, 0.38, 0.16), dry=(0.30, 0.32, 0.10), dryf=0.3, n=(16, 30)),
    'forest': dict(h=(0.08, 0.22), w=0.0050, lean=0.3, root=(0.03, 0.06, 0.012), tip=(0.16, 0.26, 0.05), dry=(0.30, 0.26, 0.10), dryf=0.2, n=(6, 14)),
}
def grass(name, bvh, pts, style, mat, scale=1.0):
    """Clumps of curved, tapered blades at the given ground points; one mesh, colour per vertex (root dark, tip light, some dry blades)."""
    S = STYLE[style]; V = []; F = []; C = []; base = 0; segs = 4
    for (x, y) in pts:
        z0 = drop(bvh, x, y); nb = rng.integers(*S['n'])
        for _ in range(nb):
            r = abs(rng.normal(0, 0.035)) * scale; t = rng.uniform(0, 2 * math.pi); bx, by = x + r * math.cos(t), y + r * math.sin(t)
            h = rng.uniform(*S['h']) * scale * (0.7 + 0.6 * rng.random()); w = S['w'] * (0.7 + 0.6 * rng.random()); lean = S['lean'] * (0.4 + rng.random())
            d = rng.uniform(0, 2 * math.pi); dx, dy = math.cos(d), math.sin(d); fa = d + math.pi / 2 + rng.normal(0, 0.5); fx, fy = math.cos(fa), math.sin(fa)
            dryb = rng.random() < S['dryf']; root = np.array(S['root']); tip = np.array(S['dry'] if dryb else S['tip']) * (0.8 + 0.4 * rng.random())
            for k in range(segs + 1):
                s = k / segs; bend = lean * h * s * s; zz = z0 - 0.01 + h * s * (1 - 0.25 * lean * s); ww = w * (1 - s) ** 0.8 + 0.0004
                cx, cy = bx + dx * bend, by + dy * bend
                V.append((cx - fx * ww, cy - fy * ww, zz)); V.append((cx + fx * ww, cy + fy * ww, zz)); c = root + (tip - root) * (s ** 0.7); C.append(c); C.append(c)
            for k in range(segs): F.append((base + 2 * k, base + 2 * k + 1, base + 2 * k + 3, base + 2 * k + 2))
            base += 2 * (segs + 1)
    return mesh_obj(name, V, F, mat, cols=np.array(C))

def flowers(name, bvh, pts, palette):
    V = []; F = []; C = []; base = 0
    for (x, y) in pts:
        z = drop(bvh, x, y) + rng.uniform(0.12, 0.3); col = np.array(palette[rng.integers(len(palette))]); r = rng.uniform(0.008, 0.016)
        for p in range(6):                       # six petals round a centre
            a0 = p * math.pi / 3 + rng.normal(0, 0.1); px, py = math.cos(a0), math.sin(a0)
            V += [(x, y, z), (x + (px * 1.0 - py * 0.35) * r, y + (py * 1.0 + px * 0.35) * r, z + 0.002), (x + px * 2.1 * r, y + py * 2.1 * r, z - 0.004), (x + (px * 1.0 + py * 0.35) * r, y + (py * 1.0 - px * 0.35) * r, z + 0.002)]
            F.append((base, base + 1, base + 2, base + 3)); C += [col * 0.7, col, col, col]; base += 4
        # stem
        z0 = drop(bvh, x, y); V += [(x - 0.0015, y, z0), (x + 0.0015, y, z0), (x + 0.0015, y, z), (x - 0.0015, y, z)]; F.append((base, base + 1, base + 2, base + 3)); C += [(0.05, 0.1, 0.02)] * 4; base += 4
    return mesh_obj(name, V, F, BLADE, cols=np.array(C), smooth=False)

def rock(name, mat, size, seed, flat=0.7, sink=0.25, jag=1.0):
    """Sculpted boulder: icosphere with large fracture planes (voronoi), medium lumps and fine grain."""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scn.collection.objects.link(ob); me.materials.append(mat)
    r2 = np.random.default_rng(seed); P = np.array([v.co[:] for v in me.vertices])
    cells = r2.normal(size=(11, 3)); cells /= np.linalg.norm(cells, axis=1, keepdims=True)
    d = P @ cells.T; facet = np.sort(d, axis=1)[:, -1]                          # the closest fracture plane flattens each region
    nrm = P / np.linalg.norm(P, axis=1, keepdims=True)
    lump = sum(np.sin(P @ r2.normal(size=3) * f + r2.uniform(0, 6)) * a for f, a in ((2.3, 0.06), (5.1, 0.03), (11.0, 0.016 * jag), (23.0, 0.007 * jag)))
    P2 = nrm * (1.0 + lump)[:, None]
    for c in cells:                                                               # cut flat fracture faces
        pl = (P2 @ c); lim = 0.62 + r2.uniform(0, 0.14); over = pl > lim; P2[over] -= np.outer(pl[over] - lim, c) * 0.97
    P2[:, 2] *= flat; P2 *= size; P2[:, 2] -= size * flat * sink
    me.vertices.foreach_set('co', P2.astype(np.float32).ravel()); me.update()
    for p in me.polygons: p.use_smooth = True
    return ob

def pebbles(name, bvh, pts, mat, smin=0.015, smax=0.06):
    V = []; F = []; base = 0
    bm0 = bmesh.new(); bmesh.ops.create_icosphere(bm0, subdivisions=1, radius=1.0); IV = np.array([v.co[:] for v in bm0.verts]); IF = [[v.index for v in f.verts] for f in bm0.faces]; bm0.free()
    for (x, y) in pts:
        s = rng.uniform(smin, smax); sc = np.array([s * rng.uniform(0.8, 1.4), s * rng.uniform(0.7, 1.1), s * rng.uniform(0.35, 0.6)]); a = rng.uniform(0, 6.28)
        R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]]); jit = 1 + rng.normal(0, 0.12, size=(len(IV), 1))
        P = (IV * jit * sc) @ R.T + (x, y, drop(bvh, x, y) - s * 0.15); V += P.tolist(); F += [[i + base for i in f] for f in IF]; base += len(IV)
    return mesh_obj(name, V, F, mat)

def field(n, mask=None):
    """Points on the big tile (x -6..6, y -4..10), full density to y = 3, thinning beyond so the far grass fades into the textured ground."""
    pts = scatter(int(n * 2.2), 6.0, 7.0, lambda x, y: np.exp(-np.clip(y + 3 - 3, 0, None) / 3.5) * (mask(x, y + 3) if mask else 1)); return [(x, y + 3) for x, y in pts]
def scatter(n, fx, fy, mask=None, oversample=4):
    """n points in [-fx, fx] x [-fy, fy] accepted by mask(x, y) -> probability."""
    out = []
    while len(out) < n:
        P = np.c_[rng.uniform(-fx, fx, n * oversample), rng.uniform(-fy, fy, n * oversample)]
        if mask is not None: P = P[rng.random(len(P)) < mask(P[:, 0], P[:, 1])]
        out += P.tolist()
    return out[:n]

def ferns(name, bvh, pts, mat):
    """Fern plants: 6-10 arching fronds, each a stem with paired leaflets that shrink toward the tip."""
    V = []; F = []; C = []; base = 0
    for (x, y) in pts:
        z0 = drop(bvh, x, y); nf = rng.integers(6, 11); size = rng.uniform(0.35, 0.7)
        for k in range(nf):
            a0 = k / nf * 6.283 + rng.normal(0, 0.25); ca, sa = math.cos(a0), math.sin(a0); L = size * rng.uniform(0.8, 1.15); up = rng.uniform(0.9, 1.4); segs = 9
            pts3 = [(x + ca * L * s, y + sa * L * s, z0 + L * up * s * (1 - s) * 0.9 + 0.01) for s in np.linspace(0, 1, segs + 1)]
            for i in range(1, segs):
                s = i / segs; lw = 0.16 * size * math.sin(math.pi * min(1, s * 1.1)) * (1 - 0.3 * s); px, py, pz = pts3[i]; nx_, ny_, nz_ = pts3[i + 1]
                for side in (-1, 1):                 # one leaflet each side: a slim diamond pointing out and a little forward
                    ox, oy = -sa * side, ca * side; tip = (px + ox * lw + ca * lw * 0.3, py + oy * lw + sa * lw * 0.3, pz - lw * 0.25)
                    V += [(px, py, pz), ((px + nx_) / 2 + ox * lw * 0.25, (py + ny_) / 2 + oy * lw * 0.25, (pz + nz_) / 2), tip, (px + ox * lw * 0.25 - ca * 0.01, py + oy * lw * 0.25 - sa * 0.01, pz)]
                    F.append((base, base + 1, base + 2, base + 3)); c0 = np.array((0.04, 0.09, 0.02)); c1 = np.array((0.16, 0.30, 0.06)) * (0.8 + 0.4 * rng.random()); C += [c0, c1, c1 * 1.15, c1]; base += 4
    return mesh_obj(name, V, F, mat, cols=np.array(C), smooth=False)

def stick(name, mat, p0, p1, r=0.025):
    d = Vector(p1) - Vector(p0); L = d.length; bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=r, depth=L, location=(Vector(p0) + Vector(p1)) / 2)
    ob = bpy.context.active_object; ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); ob.data.materials.append(mat); ob.name = name
    for p in ob.data.polygons: p.use_smooth = True
    return ob

# ------------------------------------------------------------------ light, camera
def setup(cam_loc, cam_look, lens=32, sun_el=24, sun_az=-35, strength=3.4):
    w = bpy.data.worlds.new('W'); scn.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    try: sky.sky_type = 'NISHITA'
    except Exception: pass
    try: sky.sun_elevation = math.radians(sun_el); sky.sun_rotation = math.radians(sun_az + 180); sky.sun_disc = False; sky.air_density = 1.0; sky.dust_density = 0.8
    except Exception: pass
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.30
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = strength; sd.angle = math.radians(1.5); sd.color = (1.0, 0.86, 0.68)
    so = bpy.data.objects.new('sun', sd); scn.collection.objects.link(so); so.rotation_euler = (math.radians(90 - sun_el), 0, math.radians(sun_az))
    cd = bpy.data.cameras.new('cam'); cd.lens = lens; co = bpy.data.objects.new('cam', cd); scn.collection.objects.link(co); scn.camera = co
    co.location = cam_loc; co.rotation_euler = (Vector(cam_look) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    scn.render.engine = 'CYCLES'; scn.cycles.samples = SAMP; scn.cycles.use_denoising = True; scn.render.resolution_x = W; scn.render.resolution_y = H
    scn.cycles.max_bounces = 4; scn.cycles.diffuse_bounces = 2; scn.cycles.transmission_bounces = 2
    try: scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        try: scn.view_settings.view_transform = 'Filmic'
        except Exception: pass
    scn.view_settings.exposure = 0.0

BLADE = blade_mat('GrassBlade')
STONE = pbr('Stone', 'Rock048', 2.0, box=True, tint=(0.95, 0.93, 0.9))
DCAM = ((0.0, -3.4, 1.75), (0.0, 0.2, -0.6))           # chase-camera height, looking a little down the ground
stats = {}

# ------------------------------------------------------------------ the tiles
def t_meadow():
    m = pbr('Meadow', 'Grass001', 1.6, tint=(0.95, 1.0, 0.9)); mat_scale['G'] = 1.6
    g = ground('G', m, 12, 14, 28, 'Grass001', 0.02, lambda x, y: 0.05 * np.sin(x * 0.9) * np.cos(y * 0.6)); g.location.y = 3; bvh = surface(g)
    gr = grass('grass', bvh, field(3400), 'lush', BLADE); grass('fill', bvh, field(3200), 'short', BLADE)
    flowers('flowers', bvh, field(260), [(0.95, 0.95, 0.9), (0.95, 0.80, 0.15), (0.55, 0.35, 0.85), (0.9, 0.3, 0.3)])
    stats['meadow'] = len(gr.data.polygons)
def t_dry():
    m = pbr('DryGrass', 'Grass003', 1.4, tint=(1.18, 1.05, 0.72)); mat_scale['G'] = 1.4
    g = ground('G', m, 12, 14, 28, 'Grass003', 0.02, lambda x, y: 0.08 * np.sin(x * 0.7 + 1) * np.cos(y * 0.5)); g.location.y = 3; bvh = surface(g)
    gr = grass('grass', bvh, field(1900), 'dry', BLADE); grass('fill', bvh, field(3000), 'shortdry', BLADE); pebbles('stones', bvh, field(60), STONE, 0.02, 0.07)
    stats['dry'] = len(gr.data.polygons)
def t_verge():
    asph = pbr('Asphalt', 'Asphalt010', 0.5, tint=(0.62, 0.62, 0.64), rough_add=0.05); grav = pbr('Gravel', 'Gravel022', 1.2, tint=(0.95, 0.93, 0.9)); turf = pbr('Turf', 'Grass001', 1.6)
    mat_scale['road'] = 0.5; mat_scale['shoulder'] = 1.2; mat_scale['turf'] = 1.6
    road = ground('road', asph, 4.0, 10, 12, 'Asphalt010', 0.004); road.location.x = -2.6
    sh = ground('shoulder', grav, 0.9, 10, 30, 'Gravel022', 0.02, lambda x, y: -0.03 - 0.02 * (x + 0.45)); sh.location.x = -0.15
    tf = ground('turf', turf, 4.0, 10, 24, 'Grass001', 0.02, lambda x, y: -0.06 + 0.05 * np.clip(x + 2.0, 0, 4) * 0.3 + 0.04 * np.sin(y)); tf.location.x = 2.3
    line = plain('Line', (0.85, 0.85, 0.82), 0.5); ln = ground('line', line, 0.15, 10, 4); ln.location = (-0.75, 0, 0.004)
    bvh = surface(tf); bvs = surface(sh)
    gr = grass('grass', bvh, [(x + 2.3, y) for x, y in scatter(2400, 1.95, 4.8, lambda x, y: np.clip((x + 1.95) / 0.5, 0, 1))], 'verge', BLADE); grass('fill', bvh, [(x + 2.3, y) for x, y in scatter(2200, 1.95, 4.8)], 'short', BLADE)
    grass('edge', bvs, [(x - 0.15, y) for x, y in scatter(120, 0.4, 4.8, lambda x, y: np.clip((x + 0.1) / 0.3, 0, 1))], 'verge', BLADE, 0.7)
    pebbles('stones', bvs, [(x - 0.15, y) for x, y in scatter(150, 0.42, 4.8)], STONE, 0.012, 0.035)
    post = plain('Post', (0.92, 0.92, 0.9), 0.4); cap = plain('Refl', (0.9, 0.15, 0.08), 0.2)
    for y in (-1.0, 3.2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.35, y, 0.5)); p = bpy.context.active_object; p.scale = (0.1, 0.12, 1.0); p.data.materials.append(post)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.29, y, 0.88)); c = bpy.context.active_object; c.scale = (0.01, 0.06, 0.1); c.data.materials.append(cap)
    stats['verge'] = len(gr.data.polygons)
    return ((-0.4, -3.4, 1.7), (0.6, 0.4, -0.6))
def t_forest():
    litter = pbr('Litter', 'Ground042', 1.3, tint=(1.15, 1.08, 0.95), moss='Moss002', moss_amt=-0.45); mat_scale['G'] = 1.3
    g = ground('G', litter, 12, 14, 28, 'Ground042', 0.025, lambda x, y: 0.06 * np.sin(x * 1.1) * np.cos(y * 0.8)); g.location.y = 3; bvh = surface(g)
    fern = blade_mat('Fern'); ferns('ferns', bvh, [(x, y) for x, y in field(26)], fern)
    bark = pbr('Bark', 'Rock044', 3.0, box=True, tint=(0.55, 0.42, 0.32))
    stick('branch', bark, (-1.8, -0.6, drop(bvh, -1.8, -0.6) + 0.04), (0.4, 0.3, drop(bvh, 0.4, 0.3) + 0.03), 0.045)
    stick('twig', bark, (0.2, -0.4, drop(bvh, 0.2, -0.4) + 0.02), (0.9, -0.1, drop(bvh, 0.9, -0.1) + 0.03), 0.015)
    cone = plain('Cone', (0.22, 0.13, 0.06), 0.8)
    for x, y in scatter(28, 3.0, 4.0):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.03, location=(x, y, drop(bvh, x, y) + 0.015)); c = bpy.context.active_object; c.scale = (1, 1, 1.7); c.rotation_euler = (1.4, 0, rng.uniform(0, 6)); c.data.materials.append(cone)
    gr = grass('grass', bvh, field(500, lambda x, y: 0.3 + 0.7 * (np.sin(x * 2.1) * np.cos(y * 1.7) > 0.2)), 'forest', BLADE)
    rk = rock('rock', pbr('MossRock', 'Rock044', 1.2, box=True, moss='Moss002', moss_amt=0.25), 0.55, 4); rk.location = (1.6, 2.2, drop(bvh, 1.6, 2.2))
    stats['forest'] = len(gr.data.polygons)
def t_track():
    dirt = pbr('Dirt', 'Ground067', 1.0, tint=(1.05, 1.0, 0.95)); turf = pbr('Turf', 'Grass001', 1.6); mat_scale['G'] = 1.0; mat_scale['T'] = 1.6
    rut = lambda x, y: -0.07 * (np.exp(-((x - 0.75) / 0.22) ** 2) + np.exp(-((x + 0.75) / 0.22) ** 2)) + 0.02 * np.sin(y * 1.3)
    g = ground('G', dirt, 3.0, 10, 30, 'Ground067', 0.03, rut); g.location.y = 3; bvh = surface(g)
    t1 = ground('T', turf, 3.0, 10, 20, 'Grass001', 0.02, lambda x, y: 0.01 + 0.03 * np.sin(y)); t1.location.x = 3.0; t2 = ground('T2', turf, 3.0, 10, 20, 'Grass001', 0.02, lambda x, y: 0.01 + 0.03 * np.cos(y)); t2.location.x = -3.0
    bt = surface(t1); bt2 = surface(t2)
    gr = grass('crown', bvh, scatter(500, 0.35, 4.8), 'verge', BLADE, 0.8)
    grass('sideL', bt, [(x + 2.95, y) for x, y in scatter(1300, 1.45, 4.8)], 'lush', BLADE); grass('sideR', bt2, [(x - 2.95, y) for x, y in scatter(1300, 1.45, 4.8)], 'lush', BLADE)
    grass('fillL', bt, [(x + 2.95, y) for x, y in scatter(1200, 1.45, 4.8)], 'short', BLADE); grass('fillR', bt2, [(x - 2.95, y) for x, y in scatter(1200, 1.45, 4.8)], 'short', BLADE)
    pebbles('stones', bvh, scatter(90, 1.4, 4.8), STONE, 0.012, 0.04)
    stats['track'] = len(gr.data.polygons)
    return ((0.0, -3.4, 1.8), (0.0, 0.6, -0.6))
def t_dune():
    sand = pbr('Sand', 'Ground080', 0.9, tint=(1.05, 1.0, 0.9)); mat_scale['G'] = 0.9
    g = ground('G', sand, 12, 14, 28, 'Ground080', 0.025, lambda x, y: 0.25 * np.sin(x * 0.6 + 0.5) * np.cos(y * 0.35) + 0.12 * y / 4.5); g.location.y = 3; bvh = surface(g)
    pts = []
    for cx, cy in ((-1.2, 1.0), (1.3, 2.4), (0.6, -0.4), (-2.2, 3.2), (2.4, 0.2)):
        pts += [(cx + rng.normal(0, 0.35), cy + rng.normal(0, 0.3)) for _ in range(rng.integers(40, 80))]
    gr = grass('dune', bvh, pts, 'dune', BLADE)
    shell = plain('Shell', (0.9, 0.86, 0.8), 0.5); pebbles('shells', bvh, scatter(40, 3.0, 4.0), shell, 0.01, 0.025)
    stats['dune'] = len(gr.data.polygons)
def t_outcrop():
    m = pbr('Meadow', 'Grass001', 1.6); mat_scale['G'] = 1.6
    g = ground('G', m, 12, 14, 26, 'Grass001', 0.02, lambda x, y: 0.12 * np.sin(x * 0.5) + 0.06 * y / 4.5); g.location.y = 3; bvh = surface(g)
    gm = pbr('Granite', 'Rock048', 1.1, box=True, tint=(1.05, 1.03, 1.0), moss='Moss002', moss_amt=-0.2, nstr=1.4)
    tris = 0
    for k, (x, y, s, f) in enumerate(((-0.4, 1.4, 1.05, 0.62), (0.9, 0.7, 0.55, 0.7), (-1.5, 0.2, 0.35, 0.75), (0.2, -0.5, 0.18, 0.8))):
        rk = rock('rock%d' % k, gm, s, 30 + k, f, 0.3); rk.location = (x, y, drop(bvh, x, y)); rk.rotation_euler.z = rng.uniform(0, 6); tris += len(rk.data.polygons)
    gr = grass('grass', bvh, field(2600), 'lush', BLADE); grass('fill', bvh, field(2800), 'short', BLADE)
    pebbles('stones', bvh, scatter(80, 2.0, 2.0), STONE, 0.02, 0.08)
    stats['outcrop'] = tris
def t_hero():                       # the chase-camera view down a coastal road with the new ground on both sides
    asph = pbr('Asphalt', 'Asphalt010', 0.45, tint=(0.6, 0.6, 0.62)); grav = pbr('Gravel', 'Gravel022', 1.2); turf = pbr('Turf', 'Grass001', 1.6); dry = pbr('DryGrass', 'Grass003', 1.4, tint=(1.15, 1.04, 0.74))
    for k in ('road', 'shL', 'shR', 'tL', 'tR'): mat_scale[k] = {'road': 0.45, 'shL': 1.2, 'shR': 1.2, 'tL': 1.6, 'tR': 1.4}[k]
    road = ground('road', asph, 7.0, 60, 4, 'Asphalt010', 0.004); road.location.y = 22
    shL = ground('shL', grav, 0.8, 60, 12, 'Gravel022', 0.02, lambda x, y: -0.03); shL.location = (-3.9, 22, 0); shR = ground('shR', grav, 0.8, 60, 12, 'Gravel022', 0.02, lambda x, y: -0.03); shR.location = (3.9, 22, 0)
    tL = ground('tL', turf, 14, 60, 6, 'Grass001', 0.02, lambda x, y: -0.06 + 0.06 * np.clip(-x - 6.5, 0, 9) ** 1.3 * 0.2); tL.location = (-11.3, 22, 0)
    tR = ground('tR', dry, 14, 60, 6, 'Grass003', 0.02, lambda x, y: -0.06 + 0.25 * np.sin(y * 0.15) * np.clip(x + 6.5, 0, 9) * 0.1); tR.location = (11.3, 22, 0)
    line = plain('Line', (0.85, 0.85, 0.82), 0.5); yel = plain('Yellow', (0.85, 0.62, 0.1), 0.5)
    for x, m_ in ((-3.3, line), (3.3, line)): l = ground('l%.1f' % x, m_, 0.15, 60, 2); l.location = (x, 22, 0.004)
    for y in range(-6, 52, 6): l = ground('c%d' % y, yel, 0.12, 3, 2); l.location = (0, y, 0.004)
    bL = surface(tL); bR = surface(tR)
    gr = grass('gL', bL, [(x - 11.3, y + 22) for x, y in scatter(9000, 6.9, 29, lambda x, y: np.clip((x + 7) / 2, 0, 1) * np.exp(-np.clip(y + 22, 0, 60) * 0.06) * np.exp(-np.clip(-x - 3, 0, 9) * 0.25))], 'lush', BLADE)
    grass('gR', bR, [(x + 11.3, y + 22) for x, y in scatter(11000, 6.9, 29, lambda x, y: np.exp(-np.clip(y + 22, 0, 60) * 0.06) * np.exp(-np.clip(x - 3, 0, 9) * 0.2))], 'dry', BLADE)
    gm = pbr('Granite', 'Rock048', 1.1, box=True, moss='Moss002', moss_amt=-0.35)
    for k, (x, y, s) in enumerate(((7.5, 9, 1.4), (9.5, 14, 0.8), (-8.5, 18, 1.1), (6.2, 4.0, 0.4))):
        rk = rock('r%d' % k, gm, s, 50 + k, 0.65, 0.3); rk.location = (x, y, drop(bR if x > 0 else bL, x, y))
    flowers('fl', bL, [(x - 11.3, y + 22) for x, y in scatter(500, 6.9, 12, lambda x, y: np.clip((x + 7) / 2, 0, 1))], [(0.95, 0.95, 0.9), (0.95, 0.8, 0.15)])
    stats['hero'] = len(gr.data.polygons)
    return ((2.2, -6.5, 1.25), (5.5, 9, 0.1))

def backdrop(kind):
    m = {'grass': ('Grass003', 1.0, (0.95, 1.0, 0.8)), 'dry': ('Grass003', 1.0, (1.15, 1.04, 0.74)), 'forest': ('Ground042', 1.0, (1.1, 1.05, 0.95)), 'sand': ('Ground080', 1.0, (1.05, 1.0, 0.9))}[kind]
    cols = {'grass': (0.10, 0.15, 0.035), 'dry': (0.30, 0.26, 0.11), 'forest': (0.06, 0.09, 0.025), 'sand': (0.55, 0.47, 0.33)}
    bm_ = plain('Back_' + kind, cols[kind], 1.0, spec=0.0); nt = bm_.node_tree; nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.04; nz.inputs['Detail'].default_value = 6
    cr = nt.nodes.new('ShaderNodeValToRGB'); c0 = cols[kind]; cr.color_ramp.elements[0].color = (*[v * 0.7 for v in c0], 1); cr.color_ramp.elements[1].color = (*[min(1, v * 1.6 + 0.04) for v in c0], 1)
    nt.links.new(nz.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    bd = ground('backdrop', bm_, 400, 400, 0.15, None, 0, lambda x, y: -0.3 + 0.0 * x)
    bd.location.y = 190
BACK = dict(meadow='grass', dry='dry', verge='grass', forest='forest', track='grass', dune='sand', outcrop='grass', hero='dry')
TILES = dict(meadow=t_meadow, dry=t_dry, verge=t_verge, forest=t_forest, track=t_track, dune=t_dune, outcrop=t_outcrop, hero=t_hero)
cam = TILES[NAME]() or DCAM; backdrop(BACK[NAME])
setup(*cam, lens=28 if NAME == 'hero' else 30, sun_el=17 if NAME != 'hero' else 13, sun_az=150 if NAME != 'dune' else 210, strength=4.0)
scn.render.filepath = os.path.join(OUT, NAME + '.png'); bpy.ops.render.render(write_still=True)
json.dump(stats, open(os.path.join(OUT, NAME + '.json'), 'w'))
print('DONE', NAME, stats)
