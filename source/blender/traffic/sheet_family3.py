"""Design sheet: traffic cars 03 'Tera' compact crossover, 04 'Porto' delivery van, 05 Vela taxi (original designs).
Same drawing method as sheet_mira.py / sheet_saloon.py: orthographic SVG from dimensions, numbered notes, rendered with Chrome.
python3 sheet_family3.py out.html  -> then screenshot (see __main__)."""
import math, sys
from sheet_mira import View, arc
import sheet_saloon as SAL

LINE = '#142030'; CHROME = '#c9ced4'; BLACK = '#1b1c1f'; SILVER = '#aab0b7'

def sl(g, v, pts, w=1.6, c=LINE, op=1.0, kind='s'):
    g.append(f'<path d="{v.path((kind, pts), close=False)}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" opacity="{op}"/>')
def poly(g, v, pts, fill, stroke=None, sw=1.2, kind='l', op=1.0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    g.append(f'<path d="{v.path((kind, pts))}" fill="{fill}"{st} opacity="{op}"/>')
def grads(ident, paint, hi, lo):
    return f'''<defs><linearGradient id="{ident}G" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.34" stop-color="{paint}"/><stop offset="0.46" stop-color="{hi}"/><stop offset="0.50" stop-color="{paint}"/><stop offset="0.78" stop-color="{lo}"/><stop offset="1" stop-color="{lo}"/></linearGradient>
    <linearGradient id="{ident}V" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.45" stop-color="{paint}"/><stop offset="1" stop-color="{lo}"/></linearGradient>
    <linearGradient id="{ident}Gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a4654"/><stop offset="0.45" stop-color="#151b22"/><stop offset="0.55" stop-color="#26303b"/><stop offset="1" stop-color="#0d1116"/></linearGradient>
    <linearGradient id="{ident}Lo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.28"/></linearGradient>
    <radialGradient id="{ident}Rim" cx="0.45" cy="0.4" r="0.7"><stop offset="0" stop-color="#f2f4f6"/><stop offset="0.6" stop-color="#bfc4ca"/><stop offset="1" stop-color="#80868d"/></radialGradient></defs>'''

def wheel(v, g, ident, ax, r, style):
    cx, cy = v.p(ax, r); s = r * v.sc
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s:.1f}" fill="#19191b"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s * 0.92:.1f}" fill="none" stroke="#2b2d30" stroke-width="{s * 0.05:.1f}"/>')
    if style == 'suv':          # 18" five twin-spoke, graphite with machined faces
        rr = s * 0.66
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="#222529"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 0.75:.1f}" fill="#4d5258"/>')
        g.append(f'<path d="M{cx - rr * 0.62:.1f},{cy - rr * 0.25:.1f} a{rr * 0.68:.1f},{rr * 0.68:.1f} 0 0 1 {rr * 0.30:.1f},-{rr * 0.50:.1f} l{rr * 0.10:.1f},{rr * 0.15:.1f} a{rr * 0.50:.1f},{rr * 0.50:.1f} 0 0 0 -{rr * 0.21:.1f},{rr * 0.36:.1f}z" fill="#b8322c"/>')   # red caliper
        sp = []
        for k in range(5):
            for o in (-0.13, 0.13):
                a = math.radians(k * 72 - 90) + o
                pts = [(cx + math.cos(a - 0.06) * rr * 0.24, cy + math.sin(a - 0.06) * rr * 0.24), (cx + math.cos(a - 0.05) * rr * 0.97, cy + math.sin(a - 0.05) * rr * 0.97),
                       (cx + math.cos(a + 0.05) * rr * 0.97, cy + math.sin(a + 0.05) * rr * 0.97), (cx + math.cos(a + 0.06) * rr * 0.24, cy + math.sin(a + 0.06) * rr * 0.24)]
                sp.append('M' + ' L'.join('%.1f,%.1f' % q for q in pts) + 'Z')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="none" stroke="url(#{ident}Rim)" stroke-width="{rr * 0.07:.1f}"/>')
        g.append(f'<path d="{" ".join(sp)}" fill="#3b4046" stroke="#22252a" stroke-width="0.8"/>')
        sp2 = [d for d in sp]; g.append(f'<path d="{" ".join(sp2)}" fill="url(#{ident}Rim)" opacity="0.55"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 0.26:.1f}" fill="#2e3237" stroke="#16181b"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 0.12:.1f}" fill="url(#{ident}Rim)"/>')
    else:                         # 16" steel wheel under a plain plastic cover, eight vent holes
        rr = s * 0.60
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="#7b8087" stroke="#4d5157" stroke-width="2"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 0.86:.1f}" fill="none" stroke="#5f646a" stroke-width="2"/>')
        for k in range(8):
            a = math.radians(k * 45 + 22.5)
            g.append(f'<ellipse cx="{cx + math.cos(a) * rr * 0.62:.1f}" cy="{cy + math.sin(a) * rr * 0.62:.1f}" rx="{rr * 0.13:.1f}" ry="{rr * 0.09:.1f}" transform="rotate({k * 45 + 22.5:.0f} {cx + math.cos(a) * rr * 0.62:.1f} {cy + math.sin(a) * rr * 0.62:.1f})" fill="#1d1f22"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 0.34:.1f}" fill="#3a3d42" stroke="#202225"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 0.14:.1f}" fill="#8a9097"/>')

def shell(v, half):
    m = [(-y, z) for y, z in reversed(half)]
    return v.path(('s', half), ('s', m[1:]))
def both(fn):
    for s_ in (-1, 1): fn(s_, lambda pts, s_=s_: [(s_ * y, z) for y, z in pts])
def tyres(v, g, y, r, w):
    for s_ in (-1, 1):
        x0, y0 = v.p(s_ * y - w / 2, r * 2); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w * v.sc:.1f}" height="{r * 2 * v.sc:.1f}" rx="{0.05 * v.sc:.1f}" fill="#17181a"/>')
def plate(g, v, z, txt, w=0.52):
    x0, y0 = v.p(-w / 2, z + 0.11); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w * v.sc:.1f}" height="{0.11 * v.sc:.1f}" rx="3" fill="#f2f0ea" stroke="#333"/>')
    c = v.p(0, z + 0.03); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.07 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="700" fill="#222">{txt}</text>')
def dims(v, L, H, WB, FX, txt_l, txt_wb, txt_h):
    g = []; ln = lambda x1, y1, x2, y2: g.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke="#7d786f" stroke-width="1.2"/>')
    y = v.p(0, -0.13)[1]; a, b = v.p(0, 0)[0], v.p(L, 0)[0]; ln(a, y, b, y); ln(a, y - 7, a, y + 7); ln(b, y - 7, b, y + 7)
    g.append(f'<text x="{(a + b) / 2:.1f}" y="{y + 24:.1f}" class="dim">{txt_l}</text>')
    y2 = v.p(0, -0.30)[1]; fa, ra = v.p(FX, 0)[0], v.p(FX + WB, 0)[0]; ln(fa, y2, ra, y2); ln(fa, y2 - 6, fa, y2 + 6); ln(ra, y2 - 6, ra, y2 + 6)
    g.append(f'<text x="{(fa + ra) / 2:.1f}" y="{y2 + 24:.1f}" class="dim">wheelbase {txt_wb}</text>')
    x = v.p(L + 0.14, 0)[0]; t, bt = v.p(0, H)[1], v.p(0, 0)[1]; ln(x, t, x, bt); ln(x - 7, t, x + 7, t); ln(x - 7, bt, x + 7, bt)
    g.append(f'<text x="{x + 10:.1f}" y="{(t + bt) / 2:.1f}" class="dim" text-anchor="start">{txt_h}</text>')
    gl = v.p(-0.15, 0); gr = v.p(L + 0.15, 0); g.append(f'<path d="M{gl[0]:.1f},{gl[1]:.1f} L{gr[0]:.1f},{gr[1]:.1f}" stroke="#4a4740" stroke-width="2"/>')
    return '\n'.join(g)
def mark(v, x, z, n, dx=0, dy=0):
    p = v.p(x, z); q = (p[0] + dx, p[1] + dy)
    s = f'<path d="M{p[0]:.1f},{p[1]:.1f} L{q[0]:.1f},{q[1]:.1f}" stroke="#c9a45c" stroke-width="1.3"/><circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3.5" fill="#c9a45c"/>' if (dx or dy) else ''
    return s + f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="13" fill="#c9a45c"/><text x="{q[0]:.1f}" y="{q[1] + 5.5:.1f}" font-size="15" font-weight="800" text-anchor="middle" fill="#16191d">{n}</text>'

# =====================================================================  03 TERA, compact crossover
T_L, T_W, T_H, T_WB, T_R = 4.48, 1.86, 1.68, 2.70, 0.355
T_FX = 0.86; T_RX = T_FX + T_WB
T_PAINT = ('#d9d6cf', '#f7f5f0', '#8f8b83')          # Glacier white with the black cladding reads best

def tera_side(v, ident='ts', paint=T_PAINT[0], hi=T_PAINT[1], lo=T_PAINT[2], detail=True):
    g = [grads(ident, paint, hi, lo)]; FX, RX, R = T_FX, T_RX, T_R
    top = [(0.0, 0.58), (0.025, 0.78), (0.10, 0.90), (0.50, 0.985), (1.00, 1.075), (1.27, 1.115), (1.62, 1.40), (1.95, 1.60), (2.40, 1.655), (3.40, 1.655), (4.05, 1.63), (4.32, 1.585)]
    tail = [(4.32, 1.585), (4.40, 1.45), (4.45, 1.22), (4.47, 1.00), (4.48, 0.75), (4.465, 0.50), (4.40, 0.34)]
    body = v.path(('s', top), ('s', tail), ('l', [(RX + 0.44, 0.31)]), ('s', arc(RX, R, 0.43, 4, 176)), ('l', [(FX + 0.44, 0.30)]), ('s', arc(FX, R, 0.43, 4, 176)),
                  ('l', [(0.42, 0.30), (0.30, 0.30)]), ('s', [(0.30, 0.30), (0.10, 0.33), (0.03, 0.42), (0.0, 0.58)]))
    g.append(f'<path d="{body}" fill="url(#{ident}G)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.40, 0.80), (1.6, 0.85), (3.0, 0.88), (4.47, 0.92)]), ("l", [(4.465, 0.50), (4.40, 0.34)]), ("l", [(0.30, 0.30), (0.03, 0.42)]))}" fill="url(#{ident}Lo)"/>')
    # black cladding: arch flares, sills, bumper lowers; silver skid plates
    for ax in (FX, RX):
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.50, 2, 178)), ("s", arc(ax, R, 0.43, 178, 2)))}" fill="{BLACK}"/>')
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.43, 4, 176)), ("s", arc(ax, R, 0.40, 176, 4)))}" fill="#17181b"/>')
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.40, 4, 176)))}" fill="#0b0c0e"/>')
    poly(g, v, [(FX + 0.49, 0.37), (RX - 0.49, 0.37), (RX - 0.49, 0.30), (FX + 0.49, 0.30)], BLACK)
    poly(g, v, [(FX + 0.49, 0.44), (RX - 0.49, 0.44), (RX - 0.49, 0.37), (FX + 0.49, 0.37)], '#232428')
    g.append(f'<path d="{v.path(("s", [(0.0, 0.58), (0.03, 0.42), (0.10, 0.33), (0.30, 0.30)]), ("l", [(FX - 0.48, 0.30), (FX - 0.50, 0.40)]), ("s", [(FX - 0.50, 0.40), (0.30, 0.44), (0.08, 0.50), (0.01, 0.60)]))}" fill="{BLACK}"/>')
    g.append(f'<path d="{v.path(("s", [(4.465, 0.50), (4.40, 0.34), (4.20, 0.31)]), ("l", [(RX + 0.48, 0.31), (RX + 0.50, 0.40)]), ("s", [(RX + 0.50, 0.40), (4.25, 0.44), (4.47, 0.56)]))}" fill="{BLACK}"/>')
    poly(g, v, [(0.03, 0.44), (0.12, 0.35), (0.36, 0.32), (0.36, 0.37), (0.15, 0.40), (0.06, 0.48)], SILVER, '#6e747b', 1)
    poly(g, v, [(4.46, 0.48), (4.39, 0.36), (4.18, 0.33), (4.18, 0.38), (4.37, 0.41)], SILVER, '#6e747b', 1)
    # glasshouse: floating roof over a gloss-black D-pillar
    dlo = [(1.32, 1.16), (1.62, 1.39), (1.98, 1.575), (2.6, 1.61), (3.5, 1.605), (3.98, 1.585), (4.16, 1.50), (4.22, 1.25)]
    belt = [(4.22, 1.25), (3.5, 1.22), (2.4, 1.19), (1.32, 1.16)]
    g.append(f'<path d="{v.path(("s", dlo), ("s", belt))}" fill="url(#{ident}Gl)" stroke="#0a0c0f" stroke-width="3"/>')
    poly(g, v, [(2.42, 1.612), (2.52, 1.612), (2.53, 1.195), (2.43, 1.192)], '#08090b')
    poly(g, v, [(3.40, 1.607), (3.47, 1.606), (3.46, 1.218), (3.39, 1.217)], '#08090b')
    poly(g, v, [(3.86, 1.592), (3.98, 1.585), (4.16, 1.50), (4.22, 1.25), (3.98, 1.24), (3.93, 1.40)], '#07080a')
    poly(g, v, [(1.34, 1.165), (1.63, 1.395), (1.68, 1.38), (1.45, 1.18)], '#08090b', op=0.9)
    if detail:
        sl(g, v, [(1.98, 1.60), (2.6, 1.635), (3.5, 1.63), (3.98, 1.61), (4.20, 1.51), (4.255, 1.25), (3.5, 1.222), (2.4, 1.192), (1.30, 1.16)], 2.2, '#2b2e33')
    poly(g, v, [(1.85, 1.50), (2.25, 1.59), (2.05, 1.30), (1.75, 1.26)], '#9fb4c8', op=0.16)
    poly(g, v, [(2.75, 1.58), (3.10, 1.58), (2.92, 1.27), (2.66, 1.25)], '#9fb4c8', op=0.12)
    # roof rails, roof spoiler, rear screen edge-on
    sl(g, v, [(1.98, 1.695), (2.4, 1.70), (3.4, 1.70), (4.0, 1.675)], 5, '#c4c9cf')
    for x in (2.00, 3.98): poly(g, v, [(x - 0.06, 1.645), (x + 0.06, 1.645), (x + 0.05, 1.70), (x - 0.05, 1.70)], '#111214')
    poly(g, v, [(3.98, 1.645), (4.34, 1.59), (4.37, 1.555), (4.05, 1.60)], '#101114')
    poly(g, v, [(4.30, 1.575), (4.38, 1.45), (4.425, 1.27), (4.39, 1.27), (4.345, 1.44), (4.26, 1.565)], '#0c0f13')
    if detail:
        sl(g, v, [(1.30, 1.155), (1.32, 0.95), (1.33, 0.70), (1.35, 0.44)])                           # front door leading edge
        sl(g, v, [(2.47, 1.192), (2.48, 0.80), (2.49, 0.44)])                                          # B line
        sl(g, v, [(3.44, 1.218), (3.43, 0.98), (3.33, 0.86)]); sl(g, v, arc(RX, R, 0.52, 108, 172, 6))  # rear door around the flare
        sl(g, v, [(0.10, 0.90), (0.70, 1.005), (1.26, 1.105)], 1.2, LINE, 0.55)                        # bonnet shut line
        sl(g, v, [(4.33, 1.58), (4.40, 1.42), (4.44, 1.05), (4.45, 0.62)], 1.2, LINE, 0.55)            # tailgate seam
        g.append(f'<path d="{v.path(("s", [(0.62, 1.005), (1.6, 1.065), (2.8, 1.10), (3.9, 1.135), (4.44, 1.15)]), close=False)}" fill="none" stroke="#ffffff" stroke-width="2.6" opacity="0.75"/>')
        sl(g, v, [(0.66, 0.99), (1.6, 1.05), (2.8, 1.085), (3.9, 1.12), (4.44, 1.135)], 1.4, LINE, 0.45)
        sl(g, v, [(1.40, 0.60), (2.4, 0.64), (3.30, 0.68)], 1.8, '#ffffff', 0.5); sl(g, v, [(1.40, 0.585), (2.4, 0.625), (3.30, 0.665)], 1.2, LINE, 0.35)
        # split lamps: slim DRL blade up top, main lamp low in the bumper
        g.append(f'<path d="{v.path(("s", [(0.05, 0.875), (0.35, 0.935), (0.72, 1.000)]), ("s", [(0.72, 1.000), (0.60, 0.965), (0.30, 0.905), (0.04, 0.845)]))}" fill="#1f252c" stroke="#0b0d10" stroke-width="1.5"/>')
        sl(g, v, [(0.07, 0.866), (0.36, 0.927), (0.68, 0.99)], 2.6, '#f3f7ff')
        poly(g, v, [(0.015, 0.72), (0.17, 0.735), (0.19, 0.64), (0.02, 0.625)], '#1f252c', '#0b0d10', 1.4)
        poly(g, v, [(0.03, 0.705), (0.12, 0.712), (0.13, 0.65), (0.035, 0.645)], '#dfe6ee', op=0.85)
        poly(g, v, [(0.62, 0.66), (0.74, 0.665), (0.74, 0.645), (0.62, 0.64)], '#e3922f')                 # repeater in the flare
        # mirror, handles, fuel flap
        g.append(f'<path d="{v.path(("s", [(1.46, 1.175), (1.44, 1.23), (1.51, 1.30), (1.70, 1.29), (1.72, 1.22), (1.64, 1.18)]))}" fill="{BLACK}" stroke="#0b0c0e" stroke-width="1.6"/>')
        for hx, hz in ((2.05, 1.09), (3.08, 1.115)): poly(g, v, [(hx, hz), (hx + 0.20, hz + 0.004), (hx + 0.20, hz - 0.024), (hx, hz - 0.028)], '#2a2c30', '#111', 1)
        fx_, fz_ = v.p(3.82, 1.06); g.append(f'<rect x="{fx_:.1f}" y="{fz_:.1f}" width="{0.15 * v.sc:.1f}" height="{0.11 * v.sc:.1f}" rx="5" fill="none" stroke="{LINE}" stroke-width="1.4" opacity="0.6"/>')
        # tail lamp on the shoulder, wrapping round
        poly(g, v, [(4.455, 1.245), (4.18, 1.255), (4.15, 1.19), (4.465, 1.10)], '#a3151b', '#3a0608', 1.4)
        sl(g, v, [(4.44, 1.215), (4.21, 1.225)], 2.2, '#ff5a4e', kind='l')
        poly(g, v, [(4.36, 0.47), (4.46, 0.47), (4.46, 0.45), (4.36, 0.45)], '#8b1015')
    for ax in (FX, RX): wheel(v, g, ident, ax, R, 'suv')
    return '\n'.join(g)

def tera_front(v, paint=T_PAINT[0], hi=T_PAINT[1], lo=T_PAINT[2]):
    g = [grads('tf', paint, hi, lo)]; P = lambda pts: v.path(('s', pts))
    tyres(v, g, 0.80, T_R, 0.235)
    half = [(0.0, 0.30), (0.66, 0.295), (0.90, 0.36), (0.93, 0.55), (0.93, 0.98), (0.90, 1.10), (0.80, 1.17), (0.70, 1.52), (0.60, 1.645), (0.0, 1.665)]
    g.append(f'<path d="{shell(v, half)}" fill="url(#tfV)" stroke="{LINE}" stroke-width="2.2"/>')
    def side_bits(s_, q):
        poly(g, v, q([(0.895, 0.36), (0.96, 0.41), (0.965, 0.78), (0.925, 0.82), (0.925, 0.40)]), BLACK)                       # flare
        poly(g, v, q([(0.58, 1.665), (0.62, 1.70), (0.66, 1.70), (0.65, 1.655)]), '#c4c9cf')                                    # roof rail
        g.append(f'<path d="{P(q([(0.80, 1.165), (1.05, 1.17), (1.07, 1.27), (1.01, 1.31), (0.84, 1.29)]))}" fill="{BLACK}" stroke="#0b0c0e" stroke-width="1.6"/>')
        g.append(f'<path d="{v.path(("s", q([(0.46, 0.985), (0.70, 0.995), (0.905, 0.965)])), ("s", q([(0.905, 0.935), (0.70, 0.955), (0.48, 0.95)])))}" fill="#1f252c" stroke="#0b0d10" stroke-width="1.5"/>')
        sl(g, v, q([(0.49, 0.978), (0.70, 0.987), (0.89, 0.958)]), 3, '#f3f7ff')
        x0, y0 = v.p(s_ * 0.74 - 0.13, 0.765); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.26 * v.sc:.1f}" height="{0.13 * v.sc:.1f}" rx="{0.03 * v.sc:.1f}" fill="#1f252c" stroke="#0b0d10" stroke-width="1.5"/>')
        for yy in (0.67, 0.80):
            c = v.p(s_ * yy, 0.70); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.042 * v.sc:.1f}" fill="#dfe6ee"/>')
    both(side_bits)
    g.append(f'<path d="{v.path(("s", [(0.76, 1.175), (0.66, 1.49), (0.55, 1.60), (0.0, 1.615), (-0.55, 1.60), (-0.66, 1.49), (-0.76, 1.175)]), ("s", [(-0.76, 1.175), (0.0, 1.15), (0.76, 1.175)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    poly(g, v, [(-0.40, 1.52), (0.02, 1.59), (0.22, 1.59), (-0.18, 1.22), (-0.52, 1.24)], '#9fb4c8', op=0.14)
    # tall grille between the blades, mesh pattern, "T" mark
    g.append(f'<path d="{v.path(("l", [(-0.50, 0.95), (0.50, 0.95), (0.42, 0.58), (-0.42, 0.58)]))}" fill="#121316" stroke="#08090b" stroke-width="2"/>')
    for z in (0.90, 0.84, 0.78, 0.72, 0.66, 0.62):
        k = (z - 0.58) / 0.37; wv = 0.42 + 0.08 * k
        for i in range(-6, 7):
            c = v.p(i * wv / 6.5, z); g.append(f'<rect x="{c[0] - 0.022 * v.sc:.1f}" y="{c[1] - 0.012 * v.sc:.1f}" width="{0.044 * v.sc:.1f}" height="{0.022 * v.sc:.1f}" fill="#3a3e44"/>')
    c = v.p(0, 0.78); g.append(f'<rect x="{c[0] - 0.09 * v.sc:.1f}" y="{c[1] - 0.04 * v.sc:.1f}" width="{0.18 * v.sc:.1f}" height="{0.08 * v.sc:.1f}" rx="4" fill="#121316"/><text x="{c[0]:.1f}" y="{c[1] + 0.025 * v.sc:.1f}" font-size="{0.075 * v.sc:.0f}" font-weight="900" text-anchor="middle" fill="#e4e7eb">T</text>')
    g.append(f'<path d="{v.path(("s", [(-0.92, 0.55), (0.0, 0.56), (0.92, 0.55)]), ("l", [(0.90, 0.36), (0.66, 0.295), (-0.66, 0.295), (-0.90, 0.36)]))}" fill="{BLACK}"/>')
    poly(g, v, [(-0.50, 0.51), (0.50, 0.51), (0.46, 0.41), (-0.46, 0.41)], '#0f1012', '#08090b', 1.5)
    poly(g, v, [(-0.44, 0.39), (0.44, 0.39), (0.40, 0.31), (-0.40, 0.31)], SILVER, '#6e747b', 1)
    plate(g, v, 0.405, 'AU · T3RA')
    g.append(f'<path d="{P([(-0.74, 1.06), (0.0, 1.085), (0.74, 1.06)])}" fill="none" stroke="{LINE}" stroke-width="1.3" opacity="0.5"/>')
    return '\n'.join(g)

def tera_rear(v, paint=T_PAINT[0], hi=T_PAINT[1], lo=T_PAINT[2]):
    g = [grads('tr', paint, hi, lo)]; P = lambda pts: v.path(('s', pts))
    tyres(v, g, 0.80, T_R, 0.235)
    half = [(0.0, 0.31), (0.66, 0.30), (0.90, 0.36), (0.93, 0.55), (0.93, 1.06), (0.90, 1.19), (0.80, 1.25), (0.70, 1.55), (0.60, 1.645), (0.0, 1.665)]
    g.append(f'<path d="{shell(v, half)}" fill="url(#trV)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.70, 1.27), (0.62, 1.52), (0.54, 1.575), (0.0, 1.585), (-0.54, 1.575), (-0.62, 1.52), (-0.70, 1.27)]), ("s", [(-0.70, 1.27), (0.0, 1.255), (0.70, 1.27)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    sl(g, v, [(0.0, 1.29), (-0.40, 1.50)], 2.2, '#0a0a0b', kind='l')
    g.append(f'<path d="{v.path(("s", [(-0.64, 1.645), (0.0, 1.66), (0.64, 1.645)]), ("s", [(0.62, 1.595), (0.0, 1.605), (-0.62, 1.595)]))}" fill="#101114"/>')
    x0, y0 = v.p(-0.08, 1.637); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.16 * v.sc:.1f}" height="{0.018 * v.sc:.1f}" fill="#d01a20"/>')
    def side_bits(s_, q):
        poly(g, v, q([(0.895, 0.36), (0.96, 0.41), (0.965, 0.78), (0.925, 0.82), (0.925, 0.40)]), BLACK)
        poly(g, v, q([(0.58, 1.665), (0.62, 1.70), (0.66, 1.70), (0.65, 1.655)]), '#c4c9cf')
        g.append(f'<path d="{v.path(("l", q([(0.50, 1.215), (0.90, 1.205), (0.925, 1.05), (0.80, 1.05), (0.78, 1.14), (0.50, 1.15)])))}" fill="#a3151b" stroke="#3a0608" stroke-width="1.5"/>')
        sl(g, v, q([(0.53, 1.19), (0.88, 1.183), (0.90, 1.07)]), 2.4, '#ff5a4e', kind='l')
        poly(g, v, q([(0.66, 0.50), (0.84, 0.50), (0.84, 0.475), (0.66, 0.475)]), '#8b1015')
        poly(g, v, q([(0.50, 0.44), (0.62, 0.44), (0.62, 0.41), (0.50, 0.41)]), '#e8ecf0')
    both(side_bits)
    poly(g, v, [(-0.50, 1.18), (0.50, 1.18), (0.50, 1.15), (-0.50, 1.15)], '#101114')
    c = v.p(0, 1.07); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.07 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="800" letter-spacing="7" fill="#33373c">TERA</text>')
    sl(g, v, [(-0.72, 1.25), (-0.74, 0.70), (-0.60, 0.64), (0.60, 0.64), (0.74, 0.70), (0.72, 1.25)], 1.4, LINE, 0.5)
    plate(g, v, 0.75, 'AU · T3RA')
    g.append(f'<path d="{v.path(("s", [(-0.93, 0.56), (0.0, 0.57), (0.93, 0.56)]), ("l", [(0.90, 0.36), (0.66, 0.30), (-0.66, 0.30), (-0.90, 0.36)]))}" fill="{BLACK}"/>')
    poly(g, v, [(-0.46, 0.40), (0.46, 0.40), (0.42, 0.32), (-0.42, 0.32)], SILVER, '#6e747b', 1)
    return '\n'.join(g)

# =====================================================================  04 PORTO, delivery van
V_L, V_W, V_H, V_WB, V_R = 5.12, 2.00, 2.15, 3.35, 0.345
V_FX = 0.82; V_RX = V_FX + V_WB
V_PAINT = ('#e9e9e6', '#ffffff', '#a6a7a3')
TEAL, TEAL2 = '#127a86', '#f0a92e'

def porto_side(v, ident='vs', paint=V_PAINT[0], hi=V_PAINT[1], lo=V_PAINT[2], detail=True, livery=True):
    g = [grads(ident, paint, hi, lo)]; FX, RX, R = V_FX, V_RX, V_R
    top = [(0.0, 0.56), (0.02, 0.78), (0.07, 0.95), (0.30, 1.05), (0.62, 1.12), (0.82, 1.17), (1.10, 1.58), (1.34, 1.95), (1.55, 2.10), (1.85, 2.145), (3.0, 2.15), (4.96, 2.15), (5.08, 2.12)]
    tail = [(5.08, 2.12), (5.11, 2.02), (5.12, 1.50), (5.12, 0.80), (5.11, 0.52), (5.06, 0.36)]
    body = v.path(('s', top), ('s', tail), ('l', [(RX + 0.43, 0.34)]), ('s', arc(RX, R, 0.42, 4, 176)), ('l', [(FX + 0.43, 0.34)]), ('s', arc(FX, R, 0.42, 4, 176)),
                  ('l', [(0.40, 0.34), (0.25, 0.34)]), ('s', [(0.25, 0.34), (0.08, 0.37), (0.02, 0.45), (0.0, 0.56)]))
    g.append(f'<path d="{body}" fill="url(#{ident}G)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("l", [(0.30, 0.80), (5.12, 0.80), (5.11, 0.52), (5.06, 0.36), (0.25, 0.34), (0.02, 0.45)]))}" fill="url(#{ident}Lo)"/>')
    for ax in (FX, RX):
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.42, 4, 176)), ("s", arc(ax, R, 0.39, 176, 4)))}" fill="#17181b"/>')
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.39, 4, 176)))}" fill="#0b0c0e"/>')
    # unpainted bumpers and a rubbing strip all along
    g.append(f'<path d="{v.path(("s", [(0.0, 0.56), (0.02, 0.45), (0.08, 0.37), (0.25, 0.34)]), ("l", [(FX - 0.43, 0.34), (FX - 0.40, 0.62), (0.02, 0.64)]))}" fill="{BLACK}"/>')
    poly(g, v, [(RX + 0.42, 0.34), (5.06, 0.36), (5.11, 0.52), (5.12, 0.58), (RX + 0.40, 0.58)], BLACK)
    for x0, x1 in ((FX + 0.43, RX - 0.43), (RX + 0.43, 5.0)): poly(g, v, [(x0, 0.74), (x1, 0.74), (x1, 0.66), (x0, 0.66)], '#232428')
    poly(g, v, [(FX + 0.43, 0.40), (RX - 0.43, 0.40), (RX - 0.43, 0.34), (FX + 0.43, 0.34)], '#232428')
    # cab glass (the load box has none)
    dlo = [(0.99, 1.30), (1.15, 1.58), (1.37, 1.92), (1.55, 2.04), (1.82, 2.07), (1.84, 1.30)]
    g.append(f'<path d="{v.path(("s", dlo[:5]), ("l", dlo[4:]))}" fill="url(#{ident}Gl)" stroke="#0a0c0f" stroke-width="3"/>')
    poly(g, v, [(1.20, 1.62), (1.44, 1.97), (1.56, 1.97), (1.30, 1.58)], '#9fb4c8', op=0.16)
    poly(g, v, [(0.86, 1.20), (1.36, 1.95), (1.42, 1.92), (0.95, 1.21)], '#08090b', op=0.9)                         # A pillar
    if livery:          # Aurelia Parcel fleet livery: teal swoosh, amber dot, lettering
        g.append(f'<path d="{v.path(("s", [(2.0, 0.765), (3.2, 0.80), (4.3, 0.92), (5.11, 1.12)]), ("l", [(5.115, 0.92)]), ("s", [(5.115, 0.92), (4.3, 0.79), (3.2, 0.755), (2.0, 0.75)]))}" fill="{TEAL}"/>')
        g.append(f'<path d="{v.path(("s", [(2.6, 0.83), (3.6, 0.87), (4.5, 0.99), (5.115, 1.18)]), close=False)}" fill="none" stroke="{TEAL2}" stroke-width="{0.025 * v.sc:.1f}"/>')
        c = v.p(2.34, 1.20); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.27 * v.sc:.0f}" font-family="Inter" font-weight="900" letter-spacing="2" fill="{TEAL}">AURELIA</text>')
        c = v.p(2.36, 1.00); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.12 * v.sc:.0f}" font-family="Inter" font-weight="700" letter-spacing="5" fill="#2b3a40">PARCEL · SAME DAY</text>')
        c = v.p(2.20, 1.29); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.07 * v.sc:.1f}" fill="{TEAL2}"/>')
    if detail:
        sl(g, v, [(0.93, 1.22), (0.95, 0.95), (0.98, 0.78)]); sl(g, v, arc(FX, R, 0.50, 12, 62, 6))                   # cab door front edge round the arch
        sl(g, v, [(1.88, 2.08), (1.89, 1.30), (1.90, 0.42)])                                                          # cab door back edge
        sl(g, v, [(1.96, 2.04), (1.97, 0.42)]); sl(g, v, [(3.24, 2.04), (3.25, 0.80), (3.20, 0.72)])                     # sliding door
        sl(g, v, [(1.96, 2.04), (3.24, 2.04)], 1.2, LINE, 0.6, 'l')
        poly(g, v, [(3.25, 1.60), (4.70, 1.60), (4.70, 1.575), (3.25, 1.575)], '#3a3d42')                             # sliding-door rail
        poly(g, v, [(2.06, 1.13), (2.26, 1.134), (2.26, 1.106), (2.06, 1.10)], '#2a2c30', '#111', 1)
        poly(g, v, [(1.66, 1.16), (1.82, 1.164), (1.82, 1.136), (1.66, 1.13)], '#2a2c30', '#111', 1)
        for z in (1.84, 1.72):                                                                                        # pressed ribs in the load box
            sl(g, v, [(3.30, z), (4.98, z)], 2.0, '#ffffff', 0.55, 'l'); sl(g, v, [(3.30, z - 0.012), (4.98, z - 0.012)], 1.2, LINE, 0.35, 'l')
        sl(g, v, [(5.06, 2.10), (5.07, 0.60)], 1.2, LINE, 0.55, 'l')                                                  # rear door seam
        sl(g, v, [(0.12, 1.03), (0.50, 1.10), (0.84, 1.165)], 1.2, LINE, 0.5)                                         # bonnet
        # tall headlamp wrapping round the corner, fog lamp, side markers
        poly(g, v, [(0.06, 1.035), (0.44, 1.105), (0.52, 1.09), (0.46, 0.90), (0.05, 0.87)], '#1f252c', '#0b0d10', 1.5, 's')
        sl(g, v, [(0.09, 1.01), (0.42, 1.075), (0.47, 0.93)], 2.6, '#f3f7ff')
        poly(g, v, [(0.54, 1.00), (0.64, 1.01), (0.62, 0.95), (0.53, 0.945)], '#e3922f')
        poly(g, v, [(0.03, 0.52), (0.12, 0.52), (0.12, 0.47), (0.03, 0.47)], '#dfe6ee', op=0.85)
        for x in (2.45, 3.70, 4.75): poly(g, v, [(x, 0.715), (x + 0.07, 0.715), (x + 0.07, 0.69), (x, 0.69)], '#f0a020')
        # big mirror on a stalk, tall rear lamp, high brake lamp, fuel flap
        poly(g, v, [(0.92, 1.33), (1.00, 1.36), (1.00, 1.42), (0.92, 1.40)], '#111214')
        g.append(f'<path d="{v.path(("s", [(0.98, 1.38), (0.95, 1.52), (0.98, 1.70), (1.14, 1.71), (1.16, 1.50), (1.12, 1.38)]))}" fill="{BLACK}" stroke="#0b0c0e" stroke-width="1.6"/>')
        poly(g, v, [(5.12, 1.28), (5.05, 1.28), (5.04, 0.62), (5.12, 0.62)], '#a3151b', '#3a0608', 1.3)
        sl(g, v, [(5.10, 1.25), (5.10, 0.95)], 2.2, '#ff5a4e', kind='l'); poly(g, v, [(5.12, 0.88), (5.06, 0.88), (5.06, 0.75), (5.12, 0.75)], '#e3922f')
        poly(g, v, [(4.88, 2.17), (5.04, 2.17), (5.04, 2.15), (4.88, 2.15)], '#b0131a')
        fx_, fz_ = v.p(1.98, 0.98); g.append(f'<rect x="{fx_:.1f}" y="{fz_:.1f}" width="{0.15 * v.sc:.1f}" height="{0.11 * v.sc:.1f}" rx="4" fill="none" stroke="{LINE}" stroke-width="1.3" opacity="0.5"/>')
    for ax in (FX, RX): wheel(v, g, ident, ax, R, 'van')
    return '\n'.join(g)

def porto_front(v, paint=V_PAINT[0], hi=V_PAINT[1], lo=V_PAINT[2]):
    g = [grads('vf', paint, hi, lo)]; P = lambda pts: v.path(('s', pts))
    tyres(v, g, 0.86, V_R, 0.22)
    half = [(0.0, 0.33), (0.75, 0.32), (0.97, 0.40), (1.00, 0.60), (1.00, 1.08), (0.985, 1.22), (0.95, 1.92), (0.90, 2.10), (0.80, 2.15), (0.0, 2.15)]
    g.append(f'<path d="{shell(v, half)}" fill="url(#vfV)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.90, 1.26), (0.88, 1.70), (0.84, 1.96), (0.0, 2.00), (-0.84, 1.96), (-0.88, 1.70), (-0.90, 1.26)]), ("s", [(-0.90, 1.26), (0.0, 1.235), (0.90, 1.26)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    poly(g, v, [(-0.50, 1.86), (0.0, 1.97), (0.24, 1.97), (-0.22, 1.32), (-0.62, 1.34)], '#9fb4c8', op=0.14)
    for a, b in (((-0.05, 1.27), (-0.62, 1.50)), ((0.75, 1.27), (0.18, 1.50))): sl(g, v, [a, b], 2.2, '#0a0a0b', kind='l')
    def side_bits(s_, q):
        poly(g, v, q([(0.98, 1.40), (1.06, 1.41), (1.06, 1.46), (0.98, 1.46)]), '#111214')
        g.append(f'<path d="{P(q([(1.05, 1.36), (1.20, 1.37), (1.22, 1.70), (1.08, 1.72), (1.04, 1.60)]))}" fill="{BLACK}" stroke="#0b0c0e" stroke-width="1.6"/>')
        g.append(f'<path d="{v.path(("s", q([(0.52, 1.06), (0.78, 1.08), (0.96, 1.05)])), ("s", q([(0.97, 0.88), (0.78, 0.86), (0.56, 0.88)])))}" fill="#1f252c" stroke="#0b0d10" stroke-width="1.5"/>')
        sl(g, v, q([(0.56, 1.045), (0.78, 1.062), (0.94, 1.035), (0.95, 0.92)]), 3, '#f3f7ff')
        c = v.p(s_ * 0.74, 0.955); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.05 * v.sc:.1f}" fill="#dfe6ee"/>')
        poly(g, v, q([(0.86, 0.94), (0.95, 0.94), (0.95, 0.90), (0.86, 0.90)]), '#e3922f')
        c = v.p(s_ * 0.80, 0.50); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.04 * v.sc:.1f}" fill="#dfe6ee" stroke="#0b0d10" stroke-width="2"/>')
    both(side_bits)
    g.append(f'<path d="{v.path(("l", [(-0.50, 1.02), (0.50, 1.02), (0.48, 0.74), (-0.48, 0.74)]))}" fill="#121316" stroke="#08090b" stroke-width="2"/>')
    for z in (0.97, 0.91, 0.85, 0.79): sl(g, v, [(-0.47, z), (0.47, z)], 2, '#40444a', kind='l')
    c = v.p(0, 0.88); g.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{0.07 * v.sc:.1f}" fill="#121316" stroke="#d5d9de" stroke-width="2.4"/><text x="{c[0]:.1f}" y="{c[1] + 0.03 * v.sc:.1f}" font-size="{0.085 * v.sc:.0f}" font-weight="900" text-anchor="middle" fill="#e4e7eb">P</text>')
    g.append(f'<path d="{v.path(("s", [(-1.00, 0.64), (0.0, 0.65), (1.00, 0.64)]), ("l", [(0.97, 0.40), (0.75, 0.32), (-0.75, 0.32), (-0.97, 0.40)]))}" fill="{BLACK}"/>')
    poly(g, v, [(-0.55, 0.47), (0.55, 0.47), (0.52, 0.38), (-0.52, 0.38)], '#0f1012', '#08090b', 1.5)
    plate(g, v, 0.49, 'AU · P0RT')
    g.append(f'<path d="{P([(-0.86, 1.18), (0.0, 1.195), (0.86, 1.18)])}" fill="none" stroke="{LINE}" stroke-width="1.3" opacity="0.5"/>')
    return '\n'.join(g)

def porto_rear(v, paint=V_PAINT[0], hi=V_PAINT[1], lo=V_PAINT[2]):
    g = [grads('vr', paint, hi, lo)]
    tyres(v, g, 0.86, V_R, 0.22)
    half = [(0.0, 0.36), (0.80, 0.35), (0.98, 0.42), (1.00, 0.60), (1.00, 1.95), (0.97, 2.10), (0.88, 2.15), (0.0, 2.15)]
    g.append(f'<path d="{shell(v, half)}" fill="url(#vrV)" stroke="{LINE}" stroke-width="2.2"/>')
    sl(g, v, [(-0.88, 2.08), (0.88, 2.08), (0.88, 0.60), (-0.88, 0.60), (-0.88, 2.08)], 1.4, LINE, 0.6, 'l'); sl(g, v, [(0.0, 2.08), (0.0, 0.60)], 1.6, LINE, 0.8, 'l')
    for s_ in (-1, 1):
        x0, y0 = v.p(min(s_ * 0.08, s_ * 0.76), 1.92); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.68 * v.sc:.1f}" height="{0.52 * v.sc:.1f}" rx="{0.04 * v.sc:.1f}" fill="#151b22" stroke="#08090b" stroke-width="2.5"/>')
        poly(g, v, [(s_ * 0.92, 1.28), (s_ * 0.995, 1.28), (s_ * 0.995, 0.62), (s_ * 0.92, 0.62)], '#a3151b', '#3a0608', 1.3)
        poly(g, v, [(s_ * 0.92, 0.88), (s_ * 0.995, 0.88), (s_ * 0.995, 0.76), (s_ * 0.92, 0.76)], '#e3922f')
        poly(g, v, [(s_ * 0.92, 0.75), (s_ * 0.995, 0.75), (s_ * 0.995, 0.66), (s_ * 0.92, 0.66)], '#e8ecf0')
        sl(g, v, [(s_ * 0.955, 1.25), (s_ * 0.955, 0.95)], 2.4, '#ff5a4e', kind='l')
        x0, y0 = v.p(s_ * 0.11 - 0.03, 1.12); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.06 * v.sc:.1f}" height="{0.14 * v.sc:.1f}" rx="2" fill="#2a2c30"/>')
    poly(g, v, [(-0.20, 2.14), (0.20, 2.14), (0.20, 2.115), (-0.20, 2.115)], '#d01a20')
    c = v.p(0.44, 1.28); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.08 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="800" letter-spacing="6" fill="#4a4f56">PORTO</text>')
    c = v.p(-0.44, 1.16); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.11 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="900" fill="{TEAL}">AURELIA</text>')
    g.append(f'<path d="{v.path(("l", [(-1.00, 0.58), (1.00, 0.58), (0.98, 0.42), (0.80, 0.35), (-0.80, 0.35), (-0.98, 0.42)]))}" fill="{BLACK}"/>')
    poly(g, v, [(-0.70, 0.58), (0.70, 0.58), (0.70, 0.52), (-0.70, 0.52)], '#2e3034')                                        # step
    plate(g, v, 0.39, 'AU · P0RT')
    return '\n'.join(g)

# =====================================================================  05 VELA TAXI
X_PAINT = ('#e8b623', '#f8d76a', '#9a7210')
def sign_side(g, v):
    poly(g, v, [(2.36, 1.452), (2.86, 1.452), (2.86, 1.47), (2.36, 1.47)], '#111214')
    g.append(f'<path d="{v.path(("l", [(2.40, 1.47), (2.44, 1.615), (2.78, 1.615), (2.82, 1.47)]))}" fill="#fff3c4" stroke="#3a2c06" stroke-width="1.6"/>')
    c = v.p(2.61, 1.505); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.105 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="900" fill="#111">TAXI</text>')
def taxi_side(v, ident='xs', detail=True):
    p, hi, lo = X_PAINT
    g = [SAL.side(v, ident, p, hi, lo, detail)]
    if detail:
        line = [(1.42, 0.828), (2.4, 0.845), (3.40, 0.865)]
        zf = lambda x: line[0][1] + (x - line[0][0]) * (line[2][1] - line[0][1]) / (line[2][0] - line[0][0]) - 0.035
        n = 0; x = 1.44; w = 0.06
        while x + w <= 3.36:          # two-row checker band along both doors, under the feature line
            for row in (0, 1):
                if (n + row) % 2 == 0:
                    z0 = zf(x) - row * 0.045; z1 = zf(x + w) - row * 0.045
                    poly(g, v, [(x, z0), (x + w, z1), (x + w, z1 - 0.045), (x, z0 - 0.045)], '#111214')
            x += w; n += 1
        poly(g, v, [(2.40, 0.86), (2.47, 0.86), (2.47, 0.70), (2.40, 0.70)], X_PAINT[0])          # leave the B-line clear
        sl(g, v, [(2.42, 0.87), (2.43, 0.70)])
        c = v.p(1.92, 0.58); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.085 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="900" letter-spacing="2" fill="#111">AURELIA TAXI</text>')
        c = v.p(2.95, 0.58); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.085 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="900" fill="#111">T·104</text>')
        c = v.p(1.92, 0.50); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.05 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="700" fill="#3a2c06">day and night · all over the island</text>')
    sign_side(g, v)
    return '\n'.join(g)
def sign_end(g, v):
    poly(g, v, [(-0.34, 1.448), (0.34, 1.448), (0.34, 1.47), (-0.34, 1.47)], '#111214')
    g.append(f'<path d="{v.path(("l", [(-0.30, 1.47), (-0.28, 1.615), (0.28, 1.615), (0.30, 1.47)]))}" fill="#fff3c4" stroke="#3a2c06" stroke-width="1.6"/>')
    c = v.p(0, 1.505); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.105 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="900" fill="#111">TAXI</text>')
def taxi_front(v):
    g = [SAL.front(v, *X_PAINT)]; sign_end(g, v); return '\n'.join(g)
def taxi_rear(v):
    g = [SAL.rear(v, *X_PAINT)]; sign_end(g, v)
    c = v.p(0.45, 0.83); g.append(f'<text x="{c[0]:.1f}" y="{c[1]:.1f}" font-size="{0.06 * v.sc:.0f}" text-anchor="middle" font-family="Inter" font-weight="800" fill="#d9dde2">T·104</text>')
    return '\n'.join(g)

# =====================================================================  sheet
def chips(cols):
    return ''.join(f'<span class="chip"><i style="background:linear-gradient({h},{c} 45%,{l})"></i>{n}</span>' for n, c, h, l in cols)

def build(out_html):
    Wd, Hd = 3000, 2350
    body = []; html_blocks = []
    rows = [  # (tag, title, sub, y top, ground, scale, side fn, front fn, rear fn, dims, marks, spec)
        ('TRAFFIC 03', 'TERA — COMPACT CROSSOVER', 'the tough family car: higher, wider, black-clad', 170, 640, 196, tera_side, tera_front, tera_rear,
         (T_L, T_H, T_WB, T_FX, '4,480 mm', '2,700', '1,680'),
         [(0.36, 0.93, 1, 0, -150), (2.9, 1.70, 2, 0, -60), (4.05, 1.42, 3, 90, -110), (T_RX, 0.80, 4, 70, -30), (0.25, 0.36, 5, -60, 60), (T_RX + 0.2, 0.20, 6, 120, 40)],
         ['Split lamps: slim LED blade on top, main lamps low in the bumper', 'Silver roof rails on a long flat roof', 'Gloss-black D-pillar: the roof floats; spoiler over the tailgate',
          'Black arch flares and sills (the crossover look)', 'Silver skid plates front and rear', '18" five twin-spoke alloy in graphite, red calipers'],
         ('4,480 × 1,860 × 1,680 mm · wheelbase 2,700 · 18" wheels 225/55 · 5 doors · 200 mm ground clearance',
          [('Glacier white', '#d9d6cf', '#f7f5f0', '#8f8b83'), ('Forest', '#2f4a3a', '#5f7d69', '#15241b'), ('Terracotta', '#a5502f', '#cf8160', '#5c2915'), ('Graphite', '#3e4247', '#6c7177', '#1e2023'), ('Sky blue', '#5b8db6', '#8fb7d8', '#2e5170'), ('Sand', '#b8a27c', '#dbc8a5', '#7a6646')])),
        ('TRAFFIC 04', 'PORTO — DELIVERY VAN', 'parcel vans on the town and harbour roads', 900, 1450, 172, porto_side, porto_front, porto_rear,
         (V_L, V_H, V_WB, V_FX, '5,120 mm', '3,350', '2,150'),
         [(0.30, 1.00, 1, -40, -120), (1.10, 1.55, 2, -10, -160), (2.6, 1.80, 3, 0, -100), (4.0, 1.59, 4, 60, -110), (2.9, 0.70, 5, -30, 70), (5.08, 0.95, 6, 40, 75)],
         ['Tall headlamps wrapping round the corners, fog lamps in the bumper', 'Big mirrors on stalks, cab glass only', 'Fleet livery (Aurelia Parcel) or plain fleet white',
          'Sliding side door on a rail, pressed ribs in the load box', 'Unpainted bumpers and a full-length rubbing strip, amber side markers', 'Twin rear doors with tall corner lamps and a high brake lamp'],
         ('5,120 × 2,000 × 2,150 mm (2,340 over mirrors) · wheelbase 3,350 · 16" steel wheels with covers, 215/65 · sliding side door, twin rear doors',
          [('Fleet white', '#e9e9e6', '#ffffff', '#a6a7a3'), ('Aurelia Parcel', TEAL, '#3fa5b0', '#0a4a52'), ('Silver', '#a7acb2', '#dde1e6', '#686d73'), ('Navy', '#1f2c45', '#4a5a7a', '#0d1422')])),
        ('TRAFFIC 05', 'VELA TAXI', 'the approved Vela, in island taxi dress', 1680, 2130, 196, taxi_side, taxi_front, taxi_rear,
         (SAL.L, SAL.H, SAL.WB, SAL.FX, '4,700 mm', '2,800', '1,450'),
         [(2.61, 1.56, 1, 0, -70), (2.0, 0.80, 2, -40, -120), (1.92, 0.60, 3, -120, 60), (2.95, 0.60, 4, 70, 60)],
         ['Roof sign lit at night (shows TAXI when free)', 'Black-and-yellow checker band along both doors', 'AURELIA TAXI on the front doors',
          'Fleet number on the rear doors and boot, different per car'],
         ('Same body, interior and lamps as the Vela (traffic 02) · taxi yellow paint · roof sign, checker band and lettering as decals on the same model',
          [('Taxi yellow', '#e8b623', '#f8d76a', '#9a7210')])),
    ]
    for tag, title, sub, ytop, ground, sc, fs, ff, fr, dm, marks, keys, (spec, cols) in rows:
        sv = View(90, ground, sc); body.append(fs(sv)); body.append(dims(sv, *dm))
        fv = View(1430, ground, sc); body.append(ff(fv)); rv = View(1920, ground, sc); body.append(fr(rv))
        for vv, lab in ((fv, 'FRONT'), (rv, 'REAR')): body.append(f'<text x="{vv.ox:.0f}" y="{vv.oy + 44:.0f}" class="vl" text-anchor="middle">{lab}</text>')
        body.append(f'<text x="{sv.ox:.0f}" y="{sv.oy + 112:.0f}" class="vl">SIDE (LEFT)</text>')
        for x, z, n, dx, dy in marks: body.append(mark(sv, x, z, n, dx, dy))
        if tag != 'TRAFFIC 05' or True: body.append(f'<path d="M60,{ytop - 18} L2940,{ytop - 18}" stroke="#2a2e34" stroke-width="2"/>')
        ol = ''.join(f'<li><em>{i + 1}</em>{k}</li>' for i, k in enumerate(keys))
        html_blocks.append(f'<div class="rt" style="top:{ytop}px"><i class="tag">{tag}</i><b>{title}</b><span>{sub}</span></div>'
                           f'<div class="key" style="top:{ytop + 20}px"><ol>{ol}</ol><p>{spec}</p><div class="chips">{chips(cols)}</div></div>')
    html = f'''<html><head><meta charset="utf-8"><style>body{{margin:0;background:#16191d;font-family:Inter}}
.dim{{font-size:16px;fill:#a8a39a;text-anchor:middle;letter-spacing:1px}}.vl{{font-size:14px;fill:#8d887f;letter-spacing:3px;font-weight:700}}
.h b{{font-size:44px;letter-spacing:2px;color:#e9e6df}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.rt{{position:absolute;left:60px}}.rt b{{font-size:30px;letter-spacing:2px;color:#e9e6df;vertical-align:middle}}.rt span{{font-size:18px;color:#a8a39a;margin-left:16px;vertical-align:middle}}
.key{{position:absolute;left:2260px;width:690px;color:#cfcac1;font-size:17px;line-height:1.45}}.key ol{{list-style:none;padding:0;margin:0 0 14px}}.key li{{margin:0 0 7px;padding-left:38px;position:relative}}
.key em{{font-style:normal;position:absolute;left:0;top:-1px;width:26px;height:26px;border-radius:13px;background:#c9a45c;color:#16191d;font-weight:800;font-size:15px;text-align:center;line-height:26px}}
.key p{{color:#a8a39a;font-size:15.5px;margin:0 0 12px}}.chip{{display:inline-block;margin:0 16px 8px 0;font-size:14px;color:#a8a39a}}.chip i{{display:inline-block;width:22px;height:22px;border-radius:11px;vertical-align:middle;margin-right:7px;border:1px solid #555}}
.foot{{position:absolute;left:60px;top:2290px;width:2880px;color:#8d887f;font-size:16px}}
</style></head><body style="width:{Wd}px;height:{Hd}px;position:relative">
<div class="h" style="padding:40px 60px 0"><i class="tag">TRAFFIC 03 – 05</i><b>THE REST OF THE TRAFFIC FAMILY</b><span>Design sheet for approval · crossover, delivery van and taxi to join the Mira and Vela · original designs, no real makes · modelled in Blender after approval</span></div>
<svg width="{Wd}" height="{Hd}" style="position:absolute;left:0;top:0">{"".join(body)}</svg>
{"".join(html_blocks)}
<div class="foot">MODEL (all three) · same pipeline as the Mira and Vela: field-sculpted body with real panel gaps · tinted see-through glass · simple interior (the van: cab seats and a bulkhead) · lamps as separate parts that glow at night · ~30k triangles close up, 8k mid, 1.5k far · paint colours random per car</div>
</body></html>'''
    open(out_html, 'w').write(html)

if __name__ == '__main__':
    out = sys.argv[1]; build(out)
    if len(sys.argv) > 2:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={'width': 3000, 'height': 2350}); pg.goto('file://' + __import__('os').path.abspath(out)); pg.wait_for_timeout(500)
            pg.screenshot(path=sys.argv[2], type='jpeg', quality=90, full_page=True); b.close()
