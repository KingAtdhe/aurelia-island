"""Mesh helpers shared by the Aurelia Island build scripts (Blender Python)."""
import bpy, os, math
import numpy as np

rng = np.random.default_rng(42)
OUT = 'out'
ROOT = None
TILE = 800.0
STATS = {}


def lin(hexs):
    c = np.array([int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


CUBE_F = np.array([(0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6), (0, 1, 5), (0, 5, 4),
                   (2, 6, 7), (2, 7, 3), (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5)])


def _chamfer_template():
    from scipy.spatial import ConvexHull
    P = []; ID = []
    for i in range(8):
        sgn = np.array([(i & 1) * 2 - 1, ((i >> 1) & 1) * 2 - 1, ((i >> 2) & 1) * 2 - 1], float)
        for ax in range(3): ID.append((sgn, ax)); q = sgn * 0.5 - sgn * 0.08; q[ax] = sgn[ax] * 0.5; P.append(q)
    P = np.array(P); hull = ConvexHull(P); F = hull.simplices.copy(); c = P.mean(0)
    for k, f in enumerate(F):
        n = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]])
        if np.dot(n, P[f[0]] - c) < 0: F[k] = f[::-1]
    S = np.array([s_ for s_, _ in ID]); A = np.array([a_ for _, a_ in ID]); return S, A, F
_CH = None
CHAMFER_MIN = 0.4
CHAMFER_COUNT = [0]


def box(x, y, z, sx, sy, sz, yaw=0.0):
    """Cuboid standing on z. Anything at least CHAMFER_MIN thick gets chamfered edges, so its edges catch light like real ones."""
    global _CH
    m = min(sx, sy, sz)
    if m < CHAMFER_MIN: return box_sharp(x, y, z, sx, sy, sz, yaw)
    if _CH is None: _CH = _chamfer_template()
    S, A, F = _CH; c = float(np.clip(0.035 * m, 0.03, 0.14)); h = np.array([sx / 2, sy / 2, sz / 2])
    L = S * (h - c); L[np.arange(24), A] = S[np.arange(24), A] * h[A]; L[:, 2] += sz / 2
    cs, sn = math.cos(yaw), math.sin(yaw); CHAMFER_COUNT[0] += 1
    return np.c_[x + L[:, 0] * cs - L[:, 1] * sn, y + L[:, 0] * sn + L[:, 1] * cs, z + L[:, 2]], F


def box_sharp(x, y, z, sx, sy, sz, yaw=0.0):
    L = np.array([[(i & 1) - .5, ((i >> 1) & 1) - .5, (i >> 2) & 1] for i in range(8)], float) * (sx, sy, sz)
    c, s = math.cos(yaw), math.sin(yaw)
    return np.c_[x + L[:, 0] * c - L[:, 1] * s, y + L[:, 0] * s + L[:, 1] * c, z + L[:, 2]], CUBE_F


def beam(p0, p1, w, h=None):
    h = w if h is None else h
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    ax = p1 - p0; ln = np.linalg.norm(ax); ax = ax / ln
    up = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
    ay = np.cross(up, ax); ay /= np.linalg.norm(ay); az = np.cross(ax, ay)
    L = np.array([[(i & 1), ((i >> 1) & 1) - .5, ((i >> 2) & 1) - .5] for i in range(8)], float) * (ln, w, h)
    return p0 + L[:, :1] * ax + L[:, 1:2] * ay + L[:, 2:3] * az, CUBE_F


def cyl(x, y, z, r0, r1, h, n=8, a0=0.0):
    a = np.arange(n) * 2 * np.pi / n + a0
    V = np.vstack([np.c_[x + r0 * np.cos(a), y + r0 * np.sin(a), np.full(n, z)],
                   np.c_[x + r1 * np.cos(a), y + r1 * np.sin(a), np.full(n, z + h)], [[x, y, z + h]], [[x, y, z]]])
    i = np.arange(n); j = (i + 1) % n
    F = np.vstack([np.c_[i, j, n + j], np.c_[i, n + j, n + i], np.c_[n + i, n + j, np.full(n, 2 * n)], np.c_[j, i, np.full(n, 2 * n + 1)]])
    return V, F


def cone(x, y, z, r, h, n=6, a0=0.0):
    a = np.arange(n) * 2 * np.pi / n + a0
    V = np.vstack([np.c_[x + r * np.cos(a), y + r * np.sin(a), np.full(n, z)], [[x, y, z + h]]])
    i = np.arange(n)
    return V, np.c_[i, (i + 1) % n, np.full(n, n)]


def tube(x, y, z, r0, r1, h, n=5):
    V, F = cyl(x, y, z, r0, r1, h, n)
    return V[:2 * n], F[:2 * n]


def sphere(x, y, z, rx, ry, rz, nu=7, nv=5, jit=0.0):
    V = [[0, 0, -1.0]]
    for k in range(1, nv):
        ph = -np.pi / 2 + np.pi * k / nv
        a = np.arange(nu) * 2 * np.pi / nu + k * 0.4
        V += np.c_[np.cos(ph) * np.cos(a), np.cos(ph) * np.sin(a), np.full(nu, np.sin(ph))].tolist()
    V.append([0, 0, 1.0]); V = np.array(V)
    if jit: V *= 1 + rng.uniform(-jit, jit, (len(V), 1))
    i = np.arange(nu); j = (i + 1) % nu
    F = np.c_[np.zeros(nu, int), 1 + j, 1 + i].tolist()
    for k in range(nv - 2):
        a = 1 + k * nu; b = a + nu
        F += np.c_[a + i, a + j, b + j].tolist() + np.c_[a + i, b + j, b + i].tolist()
    a = 1 + (nv - 2) * nu
    F += np.c_[a + i, a + j, np.full(nu, len(V) - 1)].tolist()
    return V * (rx, ry, rz) + (x, y, z), np.array(F)


def roof(x, y, z, sx, sy, rh, yaw, over=0.5):
    hx, hy = sx / 2 + over, sy / 2 + over
    L = np.array([(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (-hx, 0, rh), (hx, 0, rh)])
    c, s = math.cos(yaw), math.sin(yaw)
    V = np.c_[x + L[:, 0] * c - L[:, 1] * s, y + L[:, 0] * s + L[:, 1] * c, z + L[:, 2]]
    return V, np.array([(0, 1, 5), (0, 5, 4), (2, 3, 4), (2, 4, 5), (1, 2, 5), (3, 0, 4), (0, 3, 2), (0, 2, 1)])


def lathe(cx, cy, z, prof, a=1.0, b=1.0, n=32, yaw=0.0, closed=True):
    """Revolve a profile [(radius, height), ...] round an ellipse with semi-axes a, b (profile radius is a scale)."""
    ang = np.arange(n) * 2 * np.pi / n
    k = len(prof); V = np.empty((n, k, 3)); c, s = math.cos(yaw), math.sin(yaw)
    for j, (r, h) in enumerate(prof):
        lx = a * r * np.cos(ang); ly = b * r * np.sin(ang)
        V[:, j, 0] = cx + lx * c - ly * s; V[:, j, 1] = cy + lx * s + ly * c; V[:, j, 2] = z + h
    F = []
    i = np.arange(n); i2 = (i + 1) % n
    for j in range(k - 1):
        F.append(np.c_[i * k + j, i2 * k + j, i2 * k + j + 1]); F.append(np.c_[i * k + j, i2 * k + j + 1, i * k + j + 1])
    return V.reshape(-1, 3), np.vstack(F)


def rot_x(V, origin, ang):
    c, s = math.cos(ang), math.sin(ang); P = V - origin
    return np.c_[P[:, 0], P[:, 1] * c - P[:, 2] * s, P[:, 1] * s + P[:, 2] * c] + origin


def rot_z(V, origin, ang):
    c, s = math.cos(ang), math.sin(ang); P = V - origin
    return np.c_[P[:, 0] * c - P[:, 1] * s, P[:, 0] * s + P[:, 1] * c, P[:, 2]] + origin


class Buf:
    def __init__(s): s.V = []; s.F = []; s.C = []; s.U = []; s.n = 0

    def add(s, VF, color, solid=True, uv=None):
        V, F = VF; V = np.asarray(V, float); F = np.asarray(F, np.int64)
        if not len(F): return
        if solid:
            c = V.mean(0); a = V[F[:, 0]] - c; b = V[F[:, 1]] - c; d = V[F[:, 2]] - c
            if np.einsum('ij,ij->i', a, np.cross(b, d)).sum() < 0: F = F[:, ::-1]
        col = np.asarray(color, float)
        if col.ndim == 1: col = np.tile(col, (len(V), 1))
        s.V.append(V); s.F.append(F + s.n); s.C.append(col); s.n += len(V)
        s.U.append(np.zeros((len(V), 2)) if uv is None else np.asarray(uv, float))

    def arrays(s): return np.vstack(s.V), np.vstack(s.F), np.vstack(s.C), np.vstack(s.U)

    def emit(s, name, mat, smooth=True, chunk=True, uv=False, boxuv=False, tile=None):
        if not s.V: return
        V, F, C, U = s.arrays(); C = calibrate(C)
        if boxuv:                                    # unshare corners and project UVs from the dominant face axis (box mapping, 2.4 m per tile)
            V = V[F].reshape(-1, 3); C = C[F].reshape(-1, 3); F = np.arange(len(V)).reshape(-1, 3)
            n = np.abs(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])); ax = np.argmax(n, 1); ax = np.repeat(ax, 3)
            U = np.where((ax == 2)[:, None], V[:, [0, 1]], np.where((ax == 0)[:, None], V[:, [1, 2]], V[:, [0, 2]])) / 2.4; uv = True
            nf = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); nf /= np.maximum(np.linalg.norm(nf, axis=1), 1e-12)[:, None]
            key = np.c_[np.round(V * 500), np.round(np.repeat(nf, 3, 0) * 60), np.round(C * 255)].astype(np.int64)      # weld again within each flat face plane
            _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
            V, C, U = V[first], C[first], U[first]; F = inv.reshape(-1, 3)
        if chunk: make_chunked(name, V, F, C, U if uv else None, mat, smooth, tile=tile)
        else: make_obj(name, V, F, C, U if uv else None, mat, smooth)


def calibrate(C):
    """Keep albedo inside the physically plausible range (about sRGB 45-235) and take the edge off over-saturated paint."""
    C = np.asarray(C, float); l = (C * np.array([0.2126, 0.7152, 0.0722])).sum(1, keepdims=True)
    C = l + (C - l) * 0.82
    return np.clip(C, 0.026, 0.82)


def compact(V, F, *attrs):
    used = np.zeros(len(V), bool); used[F.ravel()] = True
    remap = np.cumsum(used) - 1
    return (V[used], remap[F]) + tuple(None if a is None else a[used] for a in attrs)


def make_obj(name, V, F, colors=None, uvs=None, mat=None, smooth=True, normals=None, uv2=None):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', np.asarray(V, np.float32).ravel())
    me.loops.add(len(F) * 3); me.loops.foreach_set('vertex_index', np.asarray(F, np.int32).ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set('loop_start', np.arange(len(F), dtype=np.int32) * 3)
    me.polygons.foreach_set('loop_total', np.full(len(F), 3, np.int32))
    me.update(calc_edges=True); me.validate()
    me.polygons.foreach_set('use_smooth', np.full(len(me.polygons), smooth))
    li = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li)
    if colors is not None:
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        ca.data.foreach_set('color', np.c_[np.clip(colors[li], 0, 1), np.ones(len(li))].astype(np.float32).ravel())
    if uvs is not None:
        uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.asarray(uvs, np.float32)[li].ravel())
    if uv2 is not None:
        u2 = me.uv_layers.new(name='UVBlend'); u2.data.foreach_set('uv', np.asarray(uv2, np.float32)[li].ravel())
    if normals is not None:
        try: me.normals_split_custom_set_from_vertices([tuple(v) for v in np.asarray(normals, float)])
        except Exception as e: print('custom normals failed', e)
    if mat: me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if ROOT: ob.parent = ROOT
    key = name.split('__')[0]; STATS[key] = STATS.get(key, 0) + len(F)
    return ob


def make_chunked(name, V, F, colors=None, uvs=None, mat=None, smooth=True, normals=None, uv2=None, tile=None):
    cen = V[F].mean(1); T_ = tile or TILE
    tx = np.floor(cen[:, 0] / T_).astype(int); ty = np.floor(cen[:, 1] / T_).astype(int)
    key = tx * 1000 + ty
    for k in np.unique(key):
        m = key == k
        Vc, Fc, Cc, Uc, Nc, U2 = compact(V, F[m], colors, uvs, normals, uv2)
        make_obj('%s__%d_%d' % (name, tx[m][0], ty[m][0]), Vc, Fc, Cc, Uc, mat, smooth, Nc, U2)


def nmap(name, height, strength):
    """Tangent-space normal map image from a height field (rows bottom to top)."""
    gy, gx = np.gradient(height.astype(float))
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / 2; gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / 2
    n = np.stack([-gx * strength, -gy * strength, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return make_image(name, n * 0.5 + 0.5, raw=True)


def fft_noise(n, beta, seed):
    r = np.random.default_rng(seed).normal(size=(n, n))
    fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]
    f = np.hypot(fx, fy); f[0, 0] = 1
    a = np.fft.ifft2(np.fft.fft2(r) / f ** beta).real
    a -= a.min(); return a / a.max()


def make_image(name, rgb, raw=False):
    h, w = rgb.shape[:2]; has_a = rgb.shape[2] == 4
    img = bpy.data.images.new(name, w, h, alpha=has_a)
    px = np.empty((h, w, 4), np.float32); c = np.clip(rgb[..., :3], 0, 1)
    px[..., :3] = c if raw else np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4); px[..., 3] = rgb[..., 3] if has_a else 1
    if has_a: img.alpha_mode = 'STRAIGHT'
    if raw: img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = os.path.join(OUT, 'tex_' + name + '.png'); img.file_format = 'PNG'; img.save(); img.pack()
    return img


def new_mat(name, rough=0.85, metal=0.0, color=None, image=None, vcol=False, alpha=1.0, double=False, normal=None, nstrength=1.0, cutout=False, orm=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if color is not None: b.inputs['Base Color'].default_value = (*color, 1)
    tex = vc = None
    if image is not None: tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = image
    if vcol: vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    if tex and vc:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        nt.links.new(vc.outputs['Color'], mx.inputs[6]); nt.links.new(tex.outputs['Color'], mx.inputs[7])
        nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    elif tex: nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    elif vc: nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
    if normal is not None:
        nt_ = nt.nodes.new('ShaderNodeTexImage'); nt_.image = normal; nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstrength
        nt.links.new(nt_.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    if orm is not None:                                    # packed occlusion / roughness / metallic texture (glTF convention: G = roughness, B = metallic)
        ot = nt.nodes.new('ShaderNodeTexImage'); ot.image = orm; sp = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(ot.outputs['Color'], sp.inputs[0]); nt.links.new(sp.outputs[1], b.inputs['Roughness']); nt.links.new(sp.outputs[2], b.inputs['Metallic'])
    if cutout and tex:
        rn = nt.nodes.new('ShaderNodeMath'); rn.operation = 'ROUND'; nt.links.new(tex.outputs['Alpha'], rn.inputs[0]); nt.links.new(rn.outputs[0], b.inputs['Alpha'])
        try: m.surface_render_method = 'DITHERED'
        except Exception: pass
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    m.use_backface_culling = not double
    return m
