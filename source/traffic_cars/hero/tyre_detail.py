"""Detailed traffic-car tyre: modelled sidewall (bead, rim protector, bulge, shoulder) and tread with two
circumferential grooves and a crowned face, UV-mapped to tyre_basecolor.png / tyre_normal.png (see tyre_tex.py)
for the shoulder slots, sipes, sidewall lettering and serrations.

build(bm, c, o_, R, K, kw, seg) adds the tyre to bm; profile units are the Mira ones (tread radius 0.318),
mapped with the same radial remap the old smooth tyre used, so fitment to rims and arches is unchanged.
setup_material(m) wires the two textures into the 'Tyre' material."""
import os, math, bmesh, bpy

HERE = os.path.dirname(os.path.abspath(__file__))
TEX_PITCHES = 4
PITCHES = 64                         # tread pitches round the tyre (multiple of TEX_PITCHES)
SIDE_REP = 2                         # sidewall lettering repeats round the tyre
WT = 0.068                           # half tread width (Mira units)
GROOVES = (-0.44, 0.44)              # groove centres as a fraction of WT (must match tyre_tex.TREAD_GROOVES)
GW, GD = 0.0058, 0.0075              # groove half width at the top, depth

# sidewall, bead -> shoulder, for the w < 0 side (mirrored for w > 0)
SIDE = [(0.203, -0.086), (0.214, -0.0955), (0.222, -0.1012), (0.228, -0.1016), (0.233, -0.0995),
        (0.250, -0.1018), (0.270, -0.1035), (0.290, -0.1008), (0.305, -0.0935), (0.3135, -0.0825), (0.3175, -0.0715)]
SIDE_IN = [(0.203, -0.086), (0.240, -0.1010), (0.290, -0.1008), (0.3135, -0.0825), (0.3175, -0.0715)]   # faces the car: kept light

def _crown(w): return 0.318 - 0.0016 * (w / WT) ** 2

def _tread():
    xs = [-1.0, -0.70]
    for g in GROOVES:
        xs_g = [g - GW / WT * 1.25, g - GW / WT * 0.7, g + GW / WT * 0.7, g + GW / WT * 1.25]
        if g < 0: xs += xs_g + [0.0]
        else: xs += xs_g + [0.70, 1.0]
    pts = []
    for i, x in enumerate(xs):
        w = x * WT; r = _crown(w)
        inside = any(abs(x - g) < GW / WT for g in GROOVES)
        pts.append((r - GD if inside else r, w))
    return pts

def profiles():
    """Three strips (inner sidewall, tread, outer sidewall); each point (r, w, v)."""
    def side(sgn, pts=SIDE):
        return [(r, w * sgn, 0.02 + 0.46 * (r - pts[0][0]) / (pts[-1][0] - pts[0][0])) for r, w in pts]
    inner = side(1, SIDE_IN)                                     # w < 0, bead -> shoulder
    outer = side(-1)[::-1]                              # w > 0, shoulder -> bead
    tr = [(r, w, 0.52 + 0.46 * (w / WT + 1) / 2) for r, w in _tread()]
    # join the strips at the shoulders so the mesh is closed (positions shared, UVs split)
    tr[0] = (inner[-1][0], inner[-1][1], tr[0][2]); tr[-1] = (outer[0][0], outer[0][1], tr[-1][2])
    return inner, tr, outer

def build(bm, c, o_, R, K, kw, seg=64):
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    rb = 0.203 * K
    def remap(r): r = r * K; return 0.214 + (r - rb) * (R - 0.214) / (R - rb)
    verts = {}
    def vert(k, r, w):
        key = (k % seg, round(r, 6), round(w, 6))
        if key not in verts:
            a = 2 * math.pi * (k % seg) / seg; rr = remap(r)
            verts[key] = bm.verts.new((c[0] + rr * math.cos(a), c[1] + w * kw * o_, c[2] + rr * math.sin(a)))
        return verts[key]
    for si, prof in enumerate(profiles()):
        urep = SIDE_REP if si != 1 else PITCHES / TEX_PITCHES
        flipu = (-1 if si == 0 else 1) * o_              # each sidewall reads correctly from its own side, on both sides of the car
        for k in range(seg):
            u0, u1 = flipu * urep * k / seg, flipu * urep * (k + 1) / seg
            for i in range(len(prof) - 1):
                (ra, wa, va), (rb_, wb, vb) = prof[i], prof[i + 1]
                if abs(ra - rb_) < 1e-9 and abs(wa - wb) < 1e-9: continue
                q = (vert(k, ra, wa), vert(k, rb_, wb), vert(k + 1, rb_, wb), vert(k + 1, ra, wa))
                try: f = bm.faces.new(q)
                except ValueError: continue
                for l, t in zip(f.loops, ((u0, va), (u0, vb), (u1, vb), (u1, va))): l[uv].uv = t
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

def _img(name, colour):
    p = os.path.join(HERE, name); im = bpy.data.images.get(name) or bpy.data.images.load(p)
    im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'; return im

def setup_material(m):
    nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexImage'); tc.image = _img('tyre_basecolor.png', True)
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = _img('tyre_normal.png', False)
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0
    nt.links.new(tc.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.88
