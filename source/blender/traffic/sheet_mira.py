"""Design sheet: traffic car 01 'Mira' compact hatchback (original design). Orthographic SVG drawn from dimensions, rendered with Chrome."""
import math, os
S = 250                                   # px per metre in the main views
L, W, H, WB, R = 4.25, 1.80, 1.46, 2.65, 0.318
FX, RX = 0.80, 0.80 + WB                  # axle positions from the nose
PAINT, PAINT_HI, PAINT_LO = '#d4583e', '#ec8a6c', '#8e3122'

def cr(pts, closed=False):
    """Catmull-Rom spline through pts as SVG cubic segments (without the leading M)."""
    P = list(pts); n = len(P); out = []
    for i in range(n - 1 + (1 if closed else 0)):
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]; p1 = P[i % n]; p2 = P[(i + 1) % n]; p3 = P[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append('C%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (*c1, *c2, *p2))
    return ' '.join(out)

class View:
    def __init__(s, ox, oy, sc=S, flip=False): s.ox, s.oy, s.sc, s.flip = ox, oy, sc, flip
    def p(s, x, z): return (s.ox + x * s.sc, s.oy - z * s.sc)
    def path(s, *segs, close=True):
        """segs: ('s', pts) spline or ('l', pts) straight lines; points in metres."""
        d = ''; first = True
        for kind, pts in segs:
            q = [s.p(*a) for a in pts]
            if first: d += 'M%.1f,%.1f ' % q[0]; first = False
            elif kind == 's': d += 'L%.1f,%.1f ' % q[0]
            if kind == 's': d += cr(q) + ' '
            else: d += ' '.join('L%.1f,%.1f' % a for a in (q if not d.endswith(' ') or len(d) < 2 else q)) + ' '
        return d + ('Z' if close else '')
def arc(cx, cz, r, a0, a1, n=14): return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

# ---------------- side view ----------------
def side(v, ident='side', paint=PAINT, hi=PAINT_HI, lo=PAINT_LO, detail=True):
    g = []
    top = [(0.0, 0.47), (0.025, 0.62), (0.09, 0.735), (0.45, 0.83), (0.98, 0.965), (1.38, 1.22), (1.80, 1.425), (2.6, 1.462), (3.40, 1.445), (3.82, 1.405), (3.95, 1.375)]
    tail = [(3.95, 1.375), (3.99, 1.32), (4.13, 1.07), (4.20, 0.93), (4.245, 0.72), (4.25, 0.45), (4.22, 0.29), (4.12, 0.235)]
    rarch = arc(RX, R, 0.378, 4, 176); farch = arc(FX, R, 0.378, 4, 176)
    bottom = [(RX + 0.40, 0.245)]
    body = v.path(('s', top), ('s', tail), ('l', bottom), ('s', rarch), ('l', [(FX + 0.40, 0.255)]), ('s', farch), ('l', [(0.40, 0.25), (0.30, 0.23)]), ('s', [(0.30, 0.23), (0.10, 0.25), (0.03, 0.33), (0.0, 0.47)]))
    gid = ident + 'G'
    g.append(f'''<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.36" stop-color="{paint}"/><stop offset="0.50" stop-color="{hi}" stop-opacity="1"/><stop offset="0.545" stop-color="{paint}"/><stop offset="0.80" stop-color="{lo}"/><stop offset="1" stop-color="{lo}"/></linearGradient>
    <linearGradient id="{ident}Gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a4654"/><stop offset="0.45" stop-color="#151b22"/><stop offset="0.55" stop-color="#26303b"/><stop offset="1" stop-color="#0d1116"/></linearGradient>
    <linearGradient id="{ident}Sc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5a1a10" stop-opacity="0"/><stop offset="0.25" stop-color="#5a1a10" stop-opacity="0.35"/><stop offset="0.8" stop-color="#5a1a10" stop-opacity="0.3"/><stop offset="1" stop-color="#5a1a10" stop-opacity="0"/></linearGradient>
    <radialGradient id="{ident}Rim" cx="0.45" cy="0.4" r="0.7"><stop offset="0" stop-color="#eef0f2"/><stop offset="0.6" stop-color="#b9bec4"/><stop offset="1" stop-color="#7d838a"/></radialGradient></defs>''')
    g.append(f'<path d="{body}" fill="url(#{gid})" stroke="#2a1410" stroke-width="2.2"/>')
    # dark lower sill and bumper skirts (unpainted textured black)
    g.append(f'<path d="{v.path(("l", [(1.23, 0.255), (3.03, 0.255), (3.03, 0.31)]), ("s", [(3.03, 0.31), (2.2, 0.325), (1.23, 0.31)]))}" fill="#1c1d20"/>')
    g.append(f'<path d="{v.path(("s", [(0.03, 0.33), (0.10, 0.25), (0.30, 0.23)]), ("l", [(0.40, 0.25), (0.36, 0.30)]), ("s", [(0.36, 0.30), (0.15, 0.31), (0.06, 0.36)]))}" fill="#1c1d20"/>')
    g.append(f'<path d="{v.path(("s", [(4.22, 0.29), (4.12, 0.235), (3.86, 0.245)]), ("l", [(3.84, 0.29)]), ("s", [(3.84, 0.29), (4.05, 0.29), (4.20, 0.33)]))}" fill="#1c1d20"/>')
    # wheel-arch liners
    for ax in (FX, RX):
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.378, 4, 176)), ("s", arc(ax, R, 0.35, 176, 4)))}" fill="#16171a"/>')
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.352, 4, 176)))}" fill="#0b0c0e"/>')
    # glasshouse
    dlo = [(1.07, 1.005), (1.42, 1.215), (1.80, 1.385), (2.6, 1.418), (3.32, 1.400), (3.55, 1.33), (3.74, 1.19)]
    belt = [(3.74, 1.19), (3.52, 1.115), (2.4, 1.075), (1.07, 1.005)]
    g.append(f'<path d="{v.path(("s", dlo), ("s", belt))}" fill="url(#{ident}Gl)" stroke="#0a0c0f" stroke-width="3"/>')
    # floating-roof C-pillar in gloss black, B-pillar black
    g.append(f'<path d="{v.path(("l", [(3.24, 1.405), (3.36, 1.40), (3.58, 1.31), (3.76, 1.19), (3.62, 1.14), (3.30, 1.11)]))}" fill="#08090b"/>')
    g.append(f'<path d="{v.path(("l", [(2.30, 1.418), (2.41, 1.418), (2.425, 1.074), (2.315, 1.072)]))}" fill="#08090b"/>')
    g.append(f'<path d="{v.path(("l", [(1.10, 1.012), (1.40, 1.19), (1.43, 1.16), (1.30, 1.03)]))}" fill="#08090b" opacity="0.85"/>')
    # sky reflection on the glass
    g.append(f'<path d="{v.path(("l", [(1.55, 1.30), (2.05, 1.40), (1.78, 1.19), (1.45, 1.10)]))}" fill="#9fb4c8" opacity="0.18"/>')
    g.append(f'<path d="{v.path(("l", [(2.55, 1.40), (2.95, 1.405), (2.75, 1.16), (2.48, 1.11)]))}" fill="#9fb4c8" opacity="0.12"/>')
    # tailgate glass edge seen from the side
    g.append(f'<path d="{v.path(("l", [(3.86, 1.39), (3.955, 1.37), (3.99, 1.32), (4.125, 1.075), (4.06, 1.08), (3.90, 1.33)]))}" fill="#0c0f13"/>')
    # roof-end spoiler
    g.append(f'<path d="{v.path(("s", [(3.70, 1.44), (3.86, 1.425), (3.99, 1.385)]), ("l", [(3.985, 1.36), (3.80, 1.40)]))}" fill="#101114"/>')
    # shark-fin antenna
    g.append(f'<path d="{v.path(("s", [(3.42, 1.444), (3.53, 1.50), (3.58, 1.505)]), ("l", [(3.60, 1.442)]))}" fill="#101114"/>')
    if detail:
        # shut lines
        sl = lambda pts, w=1.6, c='#4a1d14': g.append(f'<path d="{v.path(("s", pts), close=False)}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>')
        sl([(1.21, 1.00), (1.235, 0.75), (1.235, 0.45), (1.25, 0.33)])                                        # front door leading edge
        sl([(2.355, 1.07), (2.37, 0.70), (2.375, 0.33)])                                                       # B line
        sl([(3.40, 1.105), (3.33, 0.85), (3.21, 0.70)]); sl(arc(RX, 0.31, 0.44, 135, 172, 6))              # rear door trailing edge round the arch
        sl([(1.25, 0.33), (2.2, 0.335), (3.05, 0.335)])
        sl([(0.14, 0.75), (0.30, 0.64), (0.38, 0.52), (0.41, 0.42)])                                          # front bumper to fender
        sl([(4.17, 0.83), (3.98, 0.81), (3.88, 0.70), (3.86, 0.55)])                                          # rear bumper to quarter
        sl([(0.12, 0.745), (0.60, 0.845), (0.98, 0.955)], 1.2, '#6a2a1d')                                     # bonnet edge
        # body sculpt: shoulder highlight and lower concave
        g.append(f'<path d="{v.path(("s", [(0.62, 0.80), (1.6, 0.86), (2.8, 0.905), (3.85, 0.95), (4.18, 0.955)]), close=False)}" fill="none" stroke="#ffd2c0" stroke-width="2.2" opacity="0.65"/>')
        g.append(f'<path d="{v.path(("s", [(1.28, 0.55), (2.3, 0.575), (3.15, 0.605)]), ("s", [(3.15, 0.605), (2.3, 0.50), (1.28, 0.47)]))}" fill="url(#{ident}Sc)"/>')
        # headlight wrapping round the corner
        g.append(f'<path d="{v.path(("s", [(0.07, 0.735), (0.30, 0.785), (0.62, 0.835)]), ("s", [(0.62, 0.835), (0.50, 0.785), (0.28, 0.70), (0.06, 0.665)]))}" fill="#20262d" stroke="#0b0d10" stroke-width="1.5"/>')
        g.append(f'<path d="{v.path(("s", [(0.10, 0.725), (0.34, 0.77), (0.58, 0.822)]), close=False)}" fill="none" stroke="#f3f7ff" stroke-width="3.2" stroke-linecap="round"/>')
        g.append(f'<circle cx="{v.p(0.16, 0.70)[0]:.1f}" cy="{v.p(0.16, 0.70)[1]:.1f}" r="{0.035 * v.sc:.1f}" fill="#cfd7e0" stroke="#5d6670"/>')
        # side repeater, mirror, handles, fuel flap
        g.append(f'<path d="{v.path(("l", [(0.78, 0.83), (0.86, 0.84), (0.86, 0.825), (0.78, 0.817)]))}" fill="#e3922f"/>')
        g.append(f'<path d="{v.path(("s", [(1.20, 1.00), (1.17, 1.06), (1.24, 1.115), (1.41, 1.105), (1.43, 1.05), (1.36, 1.01)]))}" fill="url(#{gid})" stroke="#2a1410" stroke-width="1.8"/>')
        g.append(f'<path d="{v.path(("l", [(1.22, 1.06), (1.40, 1.08), (1.41, 1.06), (1.23, 1.04)]))}" fill="#101114"/>')
        for hx, hz in ((1.95, 0.875), (3.02, 0.91)):
            g.append(f'<path d="{v.path(("s", [(hx, hz), (hx + 0.09, hz + 0.008), (hx + 0.18, hz + 0.004)]), ("s", [(hx + 0.18, hz - 0.022), (hx + 0.09, hz - 0.026), (hx, hz - 0.02)]))}" fill="{lo}" stroke="#3a150e" stroke-width="1.2"/>')
        fx_, fz_ = v.p(3.72, 0.97); g.append(f'<rect x="{fx_:.1f}" y="{fz_:.1f}" width="{0.13 * v.sc:.1f}" height="{0.10 * v.sc:.1f}" rx="6" fill="none" stroke="#4a1d14" stroke-width="1.5"/>')
        # tail lamp wrap
        g.append(f'<path d="{v.path(("s", [(4.205, 0.985), (4.05, 1.0), (3.93, 0.975)]), ("s", [(3.93, 0.975), (3.99, 0.925), (4.225, 0.895)]))}" fill="#a3151b" stroke="#3a0608" stroke-width="1.5"/>')
        g.append(f'<path d="{v.path(("s", [(4.20, 0.955), (4.06, 0.965), (3.97, 0.955)]), close=False)}" fill="none" stroke="#ff5a4e" stroke-width="2.6" stroke-linecap="round"/>')
        g.append(f'<path d="{v.path(("l", [(4.12, 0.40), (4.24, 0.40), (4.24, 0.37), (4.12, 0.37)]))}" fill="#8b1015"/>')   # rear reflector
    # wheels
    for ax in (FX, RX):
        cx, cy = v.p(ax, R); r = R * v.sc
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#1a1b1d"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.93:.1f}" fill="none" stroke="#2c2e31" stroke-width="{r * 0.06:.1f}"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.665:.1f}" fill="#202226"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.50:.1f}" fill="#4d5157"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.30:.1f}" fill="#3a3d42"/>')
        g.append(f'<path d="M{cx + r * 0.2:.1f},{cy - r * 0.42:.1f} a{r * 0.47:.1f},{r * 0.47:.1f} 0 0 1 {r * 0.27:.1f},{r * 0.38:.1f} l-{r * 0.13:.1f},{r * 0.06:.1f} a{r * 0.33:.1f},{r * 0.33:.1f} 0 0 0 -{r * 0.18:.1f},-{r * 0.25:.1f}z" fill="#4c7fb2"/>')   # blue caliper
        spokes = []
        for k in range(5):                                       # five twin spokes, original pattern
            a = math.radians(k * 72 - 90)
            for da in (-7.5, 7.5):
                b = a + math.radians(da); b2 = a + math.radians(da * 1.6)
                pts = [(cx + math.cos(b - 0.09) * r * 0.16, cy + math.sin(b - 0.09) * r * 0.16), (cx + math.cos(b2 - 0.075) * r * 0.62, cy + math.sin(b2 - 0.075) * r * 0.62),
                       (cx + math.cos(b2 + 0.075) * r * 0.62, cy + math.sin(b2 + 0.075) * r * 0.62), (cx + math.cos(b + 0.09) * r * 0.16, cy + math.sin(b + 0.09) * r * 0.16)]
                spokes.append('M' + ' L'.join('%.1f,%.1f' % q for q in pts) + 'Z')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.665:.1f}" fill="none" stroke="url(#{ident}Rim)" stroke-width="{r * 0.06:.1f}"/><path d="{" ".join(spokes)}" fill="url(#{ident}Rim)" stroke="#6d737a" stroke-width="0.8"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.17:.1f}" fill="url(#{ident}Rim)" stroke="#6d737a"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.08:.1f}" fill="#2a2c30"/>')
        for k in range(5):
            a = math.radians(k * 72 - 54); g.append(f'<circle cx="{cx + math.cos(a) * r * 0.12:.1f}" cy="{cy + math.sin(a) * r * 0.12:.1f}" r="{r * 0.018:.1f}" fill="#3a3d42"/>')
    return '\n'.join(g)

# ---------------- front and rear (y across, z up) ----------------
def front(v, paint=PAINT, hi=PAINT_HI, lo=PAINT_LO):
    g = []; P = lambda pts: v.path(('s', pts))
    half = [(0.0, 0.24), (0.62, 0.235), (0.86, 0.30), (0.90, 0.48), (0.895, 0.80), (0.86, 0.93), (0.76, 1.03), (0.66, 1.33), (0.56, 1.44), (0.0, 1.462)]
    m = lambda pts: [(-y, z) for y, z in reversed(pts)]
    g.append(f'<defs><linearGradient id="fG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.45" stop-color="{paint}"/><stop offset="1" stop-color="{lo}"/></linearGradient></defs>')
    # tyres behind the body
    for s_ in (-1, 1):
        x0, y0 = v.p(s_ * 0.775 - 0.103, R * 2); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.206 * v.sc:.1f}" height="{R * 2 * v.sc:.1f}" rx="{0.05 * v.sc:.1f}" fill="#17181a"/>')
    g.append(f'<path d="{v.path(("s", half[:-1] + [(0.0, 1.462)]), ("s", m(half)[1:]))}" fill="url(#fG)" stroke="#2a1410" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.70, 1.02), (0.60, 1.30), (0.50, 1.40), (0.0, 1.415), (-0.50, 1.40), (-0.60, 1.30), (-0.70, 1.02)]), ("s", [(-0.70, 1.02), (0.0, 0.99), (0.70, 1.02)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    g.append(f'<path d="{v.path(("l", [(-0.35, 1.33), (0.05, 1.40), (0.25, 1.40), (-0.15, 1.08), (-0.50, 1.10)]))}" fill="#9fb4c8" opacity="0.14"/>')
    g.append(f'<rect x="{v.p(-0.06, 1.40)[0]:.1f}" y="{v.p(-0.06, 1.40)[1]:.1f}" width="{0.12 * v.sc:.1f}" height="{0.07 * v.sc:.1f}" rx="3" fill="#26292e"/>')   # camera / rain-sensor pod
    for s_ in (-1, 1):
        q = lambda pts: [(s_ * y, z) for y, z in pts]
        g.append(f'<path d="{P(q([(0.74, 1.00), (0.98, 1.00), (1.00, 1.08), (0.95, 1.12), (0.78, 1.10)]))}" fill="url(#fG)" stroke="#2a1410" stroke-width="1.8"/>')   # mirror
        g.append(f'<path d="{v.path(("s", q([(0.36, 0.80), (0.62, 0.81), (0.85, 0.79)])), ("s", q([(0.86, 0.73), (0.62, 0.705), (0.38, 0.73)])))}" fill="#20262d" stroke="#0b0d10" stroke-width="1.5"/>')
        g.append(f'<path d="{v.path(("s", q([(0.38, 0.79), (0.62, 0.80), (0.84, 0.78)])), close=False)}" fill="none" stroke="#f3f7ff" stroke-width="3.4" stroke-linecap="round"/>')
        c = v.p(s_ * 0.70, 0.745); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.032 * v.sc:.1f}" fill="#cfd7e0" stroke="#5d6670"/>')
        c = v.p(s_ * 0.53, 0.745); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.032 * v.sc:.1f}" fill="#cfd7e0" stroke="#5d6670"/>')
        g.append(f'<path d="{v.path(("l", q([(0.66, 0.47), (0.84, 0.50), (0.84, 0.36), (0.70, 0.36)])))}" fill="#1c1d20"/>')                                   # corner intake
        g.append(f'<path d="{v.path(("l", q([(0.70, 0.45), (0.82, 0.47), (0.82, 0.44), (0.70, 0.425)])))}" fill="#e3922f"/>')                                  # indicator
    g.append(f'<path d="{P([(-0.34, 0.80), (0.0, 0.812), (0.34, 0.80)])}" fill="none" stroke="#1c1d20" stroke-width="3"/>')
    # badge on the nose panel, lower grille with slats, plate
    c = v.p(0, 0.76); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.045 * v.sc:.1f}" fill="none" stroke="#d9dde2" stroke-width="3"/><path d="M{c[0] - 8:.1f},{c[1] + 6:.1f} L{c[0]:.1f},{c[1] - 7:.1f} L{c[0] + 8:.1f},{c[1] + 6:.1f}" fill="none" stroke="#d9dde2" stroke-width="2.4"/>')
    g.append(f'<path d="{v.path(("s", [(-0.58, 0.62), (0.0, 0.64), (0.58, 0.62)]), ("s", [(0.52, 0.32), (0.0, 0.30), (-0.52, 0.32)]))}" fill="#141518" stroke="#08090b" stroke-width="2"/>')
    for z in (0.57, 0.52, 0.47, 0.42, 0.37):
        g.append(f'<path d="{P([(-0.53, z), (0.0, z + 0.012), (0.53, z)])}" fill="none" stroke="#2e3136" stroke-width="2.4"/>')
    x0, y0 = v.p(-0.26, 0.56); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.52 * v.sc:.1f}" height="{0.11 * v.sc:.1f}" rx="3" fill="#f2f0ea" stroke="#333"/><text x="{v.p(0, 0.49)[0]:.1f}" y="{v.p(0, 0.49)[1]:.1f}" font-size="17" text-anchor="middle" font-family="Inter" font-weight="700" fill="#222">AU · M1RA</text>')
    return '\n'.join(g)

def rear(v, paint=PAINT, hi=PAINT_HI, lo=PAINT_LO):
    g = []; P = lambda pts: v.path(('s', pts))
    half = [(0.0, 0.25), (0.62, 0.245), (0.86, 0.30), (0.90, 0.48), (0.895, 0.86), (0.85, 0.97), (0.76, 1.07), (0.66, 1.33), (0.56, 1.44), (0.0, 1.462)]
    m = lambda pts: [(-y, z) for y, z in reversed(pts)]
    g.append(f'<defs><linearGradient id="rG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.45" stop-color="{paint}"/><stop offset="1" stop-color="{lo}"/></linearGradient></defs>')
    for s_ in (-1, 1):
        x0, y0 = v.p(s_ * 0.775 - 0.103, R * 2); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.206 * v.sc:.1f}" height="{R * 2 * v.sc:.1f}" rx="{0.05 * v.sc:.1f}" fill="#17181a"/>')
    g.append(f'<path d="{v.path(("s", half[:-1] + [(0.0, 1.462)]), ("s", m(half)[1:]))}" fill="url(#rG)" stroke="#2a1410" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.64, 1.09), (0.56, 1.30), (0.48, 1.37), (0.0, 1.38), (-0.48, 1.37), (-0.56, 1.30), (-0.64, 1.09)]), ("s", [(-0.64, 1.09), (0.0, 1.07), (0.64, 1.09)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    g.append(f'<path d="{v.path(("s", [(-0.58, 1.45), (0.0, 1.47), (0.58, 1.45)]), ("s", [(0.55, 1.40), (0.0, 1.415), (-0.55, 1.40)]))}" fill="#101114"/>')            # spoiler
    x0, y0 = v.p(-0.05, 1.43); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.10 * v.sc:.1f}" height="{0.018 * v.sc:.1f}" fill="#b0131a"/>')                        # third brake light
    # gloss black band joining the lamps across the tailgate
    g.append(f'<path d="{v.path(("s", [(-0.86, 0.985), (0.0, 1.005), (0.86, 0.985)]), ("s", [(0.88, 0.89), (0.0, 0.905), (-0.88, 0.89)]))}" fill="#0c0d10"/>')
    for s_ in (-1, 1):
        q = lambda pts: [(s_ * y, z) for y, z in pts]
        g.append(f'<path d="{v.path(("s", q([(0.42, 0.99), (0.70, 0.995), (0.87, 0.98)])), ("s", q([(0.885, 0.895), (0.70, 0.90), (0.42, 0.905)])))}" fill="#a3151b" stroke="#3a0608" stroke-width="1.5"/>')
        g.append(f'<path d="{v.path(("s", q([(0.45, 0.955), (0.70, 0.96), (0.85, 0.952)])), close=False)}" fill="none" stroke="#ff5a4e" stroke-width="3" stroke-linecap="round"/>')
        g.append(f'<path d="{v.path(("l", q([(0.58, 0.925), (0.68, 0.927), (0.68, 0.91), (0.58, 0.91)])))}" fill="#f4f4f4"/>')                                          # reverse lamp
        g.append(f'<path d="{v.path(("l", q([(0.76, 0.40), (0.86, 0.42), (0.86, 0.38), (0.76, 0.37)])))}" fill="#8b1015"/>')                                          # reflector
        g.append(f'<path d="{v.path(("l", q([(0.74, 1.12), (0.80, 1.07), (0.70, 1.04)])), close=False)}" fill="none" stroke="#4a1d14" stroke-width="1.4"/>')
    g.append(f'<text x="{v.p(0, 0.925)[0]:.1f}" y="{v.p(0, 0.925)[1]:.1f}" font-size="15" text-anchor="middle" font-family="Inter" font-weight="800" letter-spacing="6" fill="#d9dde2">MIRA</text>')
    g.append(f'<path d="{P([(-0.70, 1.06), (0.0, 1.045), (0.70, 1.06)])}" fill="none" stroke="#4a1d14" stroke-width="1.5"/>')
    g.append(f'<path d="{v.path(("s", [(-0.55, 0.86), (0.0, 0.875), (0.55, 0.86)]), ("l", [(0.50, 0.58), (-0.50, 0.58)]))}" fill="none" stroke="#4a1d14" stroke-width="1.5"/>')     # tailgate cut
    x0, y0 = v.p(-0.26, 0.80); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.52 * v.sc:.1f}" height="{0.12 * v.sc:.1f}" rx="3" fill="#f2f0ea" stroke="#333"/><text x="{v.p(0, 0.725)[0]:.1f}" y="{v.p(0, 0.725)[1]:.1f}" font-size="17" text-anchor="middle" font-family="Inter" font-weight="700" fill="#222">AU · M1RA</text>')
    g.append(f'<path d="{v.path(("s", [(-0.80, 0.46), (0.0, 0.47), (0.80, 0.46)]), ("l", [(0.84, 0.30), (-0.84, 0.30)]))}" fill="#1c1d20"/>')                                  # diffuser panel
    for y in (-0.3, -0.15, 0, 0.15, 0.3): g.append(f'<path d="{v.path(("l", [(y, 0.30), (y, 0.38)]), close=False)}" stroke="#2e3136" stroke-width="3"/>')
    return '\n'.join(g)

def top(v, paint=PAINT, hi=PAINT_HI):
    g = []
    half = [(0.0, 0.0), (0.0, 0.62), (0.06, 0.80), (0.30, 0.885), (0.80, 0.90), (2.4, 0.90), (3.6, 0.895), (4.05, 0.84), (4.22, 0.72), (4.25, 0.0)]
    m = [(x, -y) for x, y in reversed(half)]
    g.append(f'<defs><linearGradient id="tG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAINT_LO}"/><stop offset="0.3" stop-color="{paint}"/><stop offset="0.5" stop-color="{hi}"/><stop offset="0.7" stop-color="{paint}"/><stop offset="1" stop-color="{PAINT_LO}"/></linearGradient></defs>')
    g.append(f'<path d="{v.path(("s", half[1:-1]), ("s", m[1:-1]))}" fill="url(#tG)" stroke="#2a1410" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(1.02, 0.66), (1.80, 0.58), (3.35, 0.58), (3.70, 0.52)]), ("l", [(3.70, -0.52)]), ("s", [(3.70, -0.52), (3.35, -0.58), (1.80, -0.58), (1.02, -0.66)]), ("s", [(1.02, -0.66), (0.98, 0.0), (1.02, 0.66)]))}" fill="#151b22"/>')
    g.append(f'<path d="{v.path(("s", [(1.82, 0.54), (2.6, 0.565), (3.36, 0.545)]), ("l", [(3.36, -0.545)]), ("s", [(3.36, -0.545), (2.6, -0.565), (1.82, -0.54)]))}" fill="url(#tG)" stroke="#2a1410" stroke-width="1.4"/>')   # roof
    g.append(f'<path d="{v.path(("l", [(3.75, 0.50), (3.97, 0.46), (3.97, -0.46), (3.75, -0.50)]))}" fill="#101114"/>')
    for s_ in (-1, 1):
        g.append(f'<path d="{v.path(("l", [(1.20, s_ * 0.90), (1.24, s_ * 1.00), (1.42, s_ * 1.00), (1.40, s_ * 0.90)]))}" fill="{paint}" stroke="#2a1410" stroke-width="1.4"/>')
        g.append(f'<path d="{v.path(("s", [(0.06, s_ * 0.62), (0.12, s_ * 0.80), (0.42, s_ * 0.88)]), close=False)}" fill="none" stroke="#f3f7ff" stroke-width="3"/>')
        g.append(f'<path d="{v.path(("s", [(0.98, s_ * 0.62), (0.40, s_ * 0.60), (0.08, s_ * 0.40)]), close=False)}" fill="none" stroke="#6a2a1d" stroke-width="1.4"/>')
    g.append(f'<path d="{v.path(("l", [(3.42, 0.0), (3.60, 0.0)]), close=False)}" stroke="#101114" stroke-width="7" stroke-linecap="round"/>')
    return '\n'.join(g)

def dims_side(v):
    g = []; y = v.p(0, -0.12)[1]; a, b = v.p(0, 0)[0], v.p(L, 0)[0]
    ln = lambda x1, y1, x2, y2: g.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke="#7d786f" stroke-width="1.2"/>')
    ln(a, y, b, y); ln(a, y - 8, a, y + 8); ln(b, y - 8, b, y + 8)
    g.append(f'<text x="{(a + b) / 2:.1f}" y="{y + 26:.1f}" class="dim">4,250 mm</text>')
    y2 = v.p(0, -0.30)[1]; fa, ra = v.p(FX, 0)[0], v.p(RX, 0)[0]; ln(fa, y2, ra, y2); ln(fa, y2 - 6, fa, y2 + 6); ln(ra, y2 - 6, ra, y2 + 6)
    g.append(f'<text x="{(fa + ra) / 2:.1f}" y="{y2 + 26:.1f}" class="dim">wheelbase 2,650</text>')
    x = v.p(L + 0.16, 0)[0]; t, bt = v.p(0, H)[1], v.p(0, 0)[1]; ln(x, t, x, bt); ln(x - 8, t, x + 8, t); ln(x - 8, bt, x + 8, bt)
    g.append(f'<text x="{x + 12:.1f}" y="{(t + bt) / 2:.1f}" class="dim" text-anchor="start">1,460</text>')
    gl = v.p(-0.15, 0); gr = v.p(L + 0.15, 0); g.append(f'<path d="M{gl[0]:.1f},{gl[1]:.1f} L{gr[0]:.1f},{gr[1]:.1f}" stroke="#4a4740" stroke-width="2"/>')
    return '\n'.join(g)

def callout(x, y, tx, ty, txt):
    return f'<path d="M{x},{y} L{tx},{ty}" stroke="#c9a45c" stroke-width="1.3"/><circle cx="{x}" cy="{y}" r="4" fill="#c9a45c"/><text x="{tx + (6 if tx >= x else -6)}" y="{ty + (-10 if tx < 200 else 5)}" class="co" text-anchor="{"start" if tx >= x or tx < 200 else "end"}">{txt}</text>'

# ---------------- family line-up silhouettes ----------------
def silhouette(v, kind):
    if kind == 'saloon':
        top_ = [(0, 0.50), (0.05, 0.70), (0.9, 0.86), (1.30, 0.94), (1.95, 1.40), (2.95, 1.43), (3.65, 1.12), (4.30, 1.02), (4.68, 0.95), (4.70, 0.50), (4.62, 0.26)]; fx, rx, r = 0.92, 3.72, 0.32
    elif kind == 'suv':
        top_ = [(0, 0.55), (0.06, 0.88), (0.85, 1.05), (1.25, 1.12), (1.80, 1.66), (3.70, 1.68), (4.30, 1.58), (4.45, 1.12), (4.48, 0.55), (4.40, 0.32)]; fx, rx, r = 0.86, 3.56, 0.36
    elif kind == 'van':
        top_ = [(0, 0.55), (0.05, 0.95), (0.55, 1.12), (1.05, 1.95), (1.40, 2.15), (5.05, 2.15), (5.10, 2.05), (5.12, 0.55), (5.05, 0.32)]; fx, rx, r = 0.80, 4.15, 0.35
    else:
        top_ = [(0.0, 0.47), (0.09, 0.735), (0.98, 0.965), (1.80, 1.425), (3.40, 1.445), (3.95, 1.375), (4.13, 1.07), (4.25, 0.72), (4.25, 0.45), (4.12, 0.235)]; fx, rx, r = FX, RX, R
    end = top_[-1]
    d = v.path(('s', top_), ('l', [(rx + 0.40, 0.25)]), ('s', arc(rx, 0.31, 0.40, 8, 172)), ('l', [(fx + 0.40, 0.25)]), ('s', arc(fx, 0.31, 0.40, 8, 172)), ('l', [(0.10, 0.25), (0, 0.47)]))
    out = f'<path d="{d}" fill="#3a3f46" stroke="#5a6069" stroke-width="1.5"/>'
    for a in (fx, rx):
        c = v.p(a, r); out += f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r * v.sc:.1f}" fill="#1a1b1d"/><circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r * v.sc * 0.6:.1f}" fill="#5c626a"/>'
    return out

PALETTE = [('Coral', '#d4583e', '#ec8a6c', '#8e3122'), ('Harbour blue', '#2f6fa3', '#5f9acb', '#1a3f60'), ('Pebble white', '#e7e4dc', '#ffffff', '#a9a59c'),
           ('Graphite', '#4a4e54', '#787d84', '#26292d'), ('Olive', '#6f7a4c', '#97a36f', '#3f4629'), ('Lemon', '#e4c34a', '#f6dd7a', '#9c7f1e')]

def build(out_html):
    Wd, Hd = 3000, 1860
    sv = View(110, 690); body = [side(sv), dims_side(sv)]
    fv = View(1690, 690); body.append(front(fv)); rv = View(2550, 690); body.append(rear(rv))
    for vv, lab in ((fv, 'FRONT'), (rv, 'REAR')):
        body.append(f'<text x="{vv.ox:.0f}" y="{vv.oy + 50:.0f}" class="vl" text-anchor="middle">{lab}</text>')
    body.append(f'<text x="{sv.ox:.0f}" y="{sv.oy + 130:.0f}" class="vl">SIDE (LEFT)</text>')
    w = lambda x, z: sv.p(x, z)
    co = [callout(*map(int, w(0.33, 0.78)), 120, 236, 'Wrap-round headlamp: LED blade + projector'), callout(*map(int, w(3.55, 1.27)), 1000, 300, 'Gloss-black C-pillar: "floating" roof'),
          callout(*map(int, w(3.86, 1.41)), 1180, 360, 'Roof spoiler + shark-fin aerial'), callout(*map(int, w(2.3, 0.53)), 720, 860, 'Soft concave sculpt along both doors'),
          callout(*map(int, w(1.6, 0.86)), 640, 236, 'Shoulder line rising to the tail'), callout(*map(int, w(RX + 0.12, 0.40)), 1230, 860, '16" five-twin-spoke alloy, blue calipers')]
    body += co
    tv = View(110, 1180, 160); body.append(top(tv)); body.append(f'<text x="{tv.ox:.0f}" y="{tv.oy + 175:.0f}" class="vl">TOP</text>')
    # paint variants: little side views
    pal = []
    for i, (n, c, hi, lo) in enumerate(PALETTE):
        vv = View(900 + (i % 3) * 330, 1120 + (i // 3) * 230, 68)
        pal.append(side(vv, 'p%d' % i, c, hi, lo, detail=False)); pal.append(f'<text x="{vv.ox + 145:.0f}" y="{vv.oy + 34:.0f}" class="sub" text-anchor="middle">{n}</text>')
    body += pal
    body.append('<text x="900" y="985" class="lbl">TRAFFIC PAINTS (RANDOM PER CAR)</text>')
    # zoomed details from the side view
    zooms = [((0.0, 0.58, 0.70, 0.92), 'Headlamp'), ((3.85, 0.86, 4.27, 1.06), 'Tail lamp'), ((RX - 0.36, -0.02, RX + 0.36, 0.66), 'Wheel')]
    zx = 1960
    body.append(f'<text x="{zx}" y="985" class="lbl">DETAILS</text>')
    for k, ((x0, z0, x1, z1), lab) in enumerate(zooms):
        a = sv.p(x0, z1); b = sv.p(x1, z0); ww, hh = b[0] - a[0], b[1] - a[1]
        bw = 300; bh = 230
        body.append(f'<svg x="{zx + k * 330}" y="1005" width="{bw}" height="{bh}" viewBox="{a[0]:.1f} {a[1]:.1f} {ww:.1f} {hh:.1f}" preserveAspectRatio="xMidYMid meet"><rect x="{a[0] - 50}" y="{a[1] - 50}" width="{ww + 100}" height="{hh + 100}" fill="#1e2227"/><use href="#sideAll"/></svg>')
        body.append(f'<text x="{zx + k * 330 + bw / 2}" y="1262" class="sub" text-anchor="middle">{lab}</text>')
    # family line-up
    lu = []
    for i, (kind, name, note) in enumerate((('hatch', '01 · Mira', 'Compact hatchback'), ('saloon', '02 · Saloon', 'Four-door family car'), ('suv', '03 · SUV', 'Compact crossover'), ('van', '04 · Van', 'Delivery van'), ('saloon', '05 · Taxi', 'Saloon in taxi livery'))):
        vv = View(1960 + (i % 3) * 330, 1440 + (i // 3) * 200, 52)
        lu.append(silhouette(vv, kind))
        if i == 0: lu.append(f'<rect x="{vv.ox - 12}" y="{vv.oy - 130}" width="300" height="175" rx="8" fill="none" stroke="#c9a45c" stroke-width="2"/>')
        lu.append(f'<text x="{vv.ox:.0f}" y="{vv.oy + 34:.0f}" class="cap2">{name}</text><text x="{vv.ox + 118:.0f}" y="{vv.oy + 34:.0f}" class="sub">{note}</text>')
    body += lu
    body.append('<text x="1960" y="1300" class="lbl">THE TRAFFIC FAMILY (ONE SHEET EACH)</text>')
    side_main = body[0]
    html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter}}
.dim{{font-size:17px;fill:#a8a39a;text-anchor:middle;letter-spacing:1px}}.vl{{font-size:14px;fill:#8d887f;letter-spacing:3px;font-weight:700}}
.co{{font-size:16px;fill:#e9e6df}}.sub{{font-size:15px;fill:#a8a39a}}.lbl{{font-size:14px;fill:#8d887f;letter-spacing:3px;font-weight:700}}.cap2{{font-size:16px;fill:#e9e6df;font-weight:800}}
.h b{{font-size:44px;letter-spacing:2px;color:#e9e6df}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.spec{{position:absolute;left:60px;top:1440px;width:1800px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:34px;color:#a8a39a;font-size:16px;line-height:1.55}}.spec b{{color:#e9e6df;display:block;font-size:14px;letter-spacing:3px;color:#8d887f;margin-bottom:8px}}
</style></head><body style="width:{Wd}px;height:{Hd}px;position:relative">
<div class="h" style="padding:46px 60px 0"><i class="tag">TRAFFIC 01</i><b>MIRA — COMPACT HATCHBACK</b><span>Design sheet for approval · the most common car on Aurelia's roads · original design, no real make · modelled in Blender after approval</span></div>
<svg width="{Wd}" height="{Hd}" style="position:absolute;left:0;top:0"><defs><g id="sideAll">{side(View(110, 690), 'z')}</g></defs>{"".join(body)}</svg>
<div class="spec">
<div><b>DIMENSIONS</b>4,250 × 1,800 × 1,460 mm · wheelbase 2,650 · 16" wheels, 205/55 tyres · 5 doors · front-wheel drive<br>Friendly, rounded small car: short bonnet, long roof, upright tail, wheels pushed to the corners.</div>
<div><b>MODEL</b>Body with real panel gaps and thickness · separate glass (tinted, see-through) · simple interior visible through the windows (seats, dash, wheel) · lights as separate parts so they glow at night: headlamps, brake lamps, indicators, reverse.<br>~30k triangles close up · 8k mid · 1.5k far.</div>
<div><b>MATERIALS</b>Metallic paint with clear coat in six traffic colours · textured black plastic on bumpers, sills and arch liners · gloss black C-pillar and spoiler · machined-silver alloys · rubber tyres with tread · red and amber lenses.</div>
</div></body></html>'''
    open(out_html, 'w').write(html)

if __name__ == '__main__':
    import sys; build(sys.argv[1])
