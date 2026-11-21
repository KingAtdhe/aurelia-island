"""Design sheet: traffic car 02 'Vela' four-door family saloon (original design). Same drawing method and layout as sheet_mira.py."""
import math, sys
from sheet_mira import cr, View, arc, callout, silhouette as mira_silhouette

L, W, H, WB, R = 4.70, 1.84, 1.45, 2.80, 0.335
FX, RX = 0.93, 0.93 + WB
PAINT, PAINT_HI, PAINT_LO = '#3f5f82', '#7d9dbf', '#1f3249'
LINE = '#142030'
CHROME = '#c9ced4'

def tyre_wheel(v, g, ident, ax):
    cx, cy = v.p(ax, R); r = R * v.sc
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#19191b"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.92:.1f}" fill="none" stroke="#2b2d30" stroke-width="{r * 0.05:.1f}"/>')
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.70:.1f}" fill="#2a2d31"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.52:.1f}" fill="#55595f"/>')
    g.append(f'<path d="M{cx - r * 0.42:.1f},{cy - r * 0.18:.1f} a{r * 0.46:.1f},{r * 0.46:.1f} 0 0 1 {r * 0.20:.1f},-{r * 0.33:.1f} l{r * 0.07:.1f},{r * 0.11:.1f} a{r * 0.33:.1f},{r * 0.33:.1f} 0 0 0 -{r * 0.14:.1f},{r * 0.24:.1f}z" fill="#8b9096"/>')   # silver caliper
    sp = []; dk = []
    for k in range(10):                                           # ten spokes, alternate machined / graphite face
        a = math.radians(k * 36 - 90)
        pts = [(cx + math.cos(a - 0.10) * r * 0.17, cy + math.sin(a - 0.10) * r * 0.17), (cx + math.cos(a - 0.045) * r * 0.68, cy + math.sin(a - 0.045) * r * 0.68),
               (cx + math.cos(a + 0.065) * r * 0.68, cy + math.sin(a + 0.065) * r * 0.68), (cx + math.cos(a + 0.07) * r * 0.17, cy + math.sin(a + 0.07) * r * 0.17)]
        d = 'M' + ' L'.join('%.1f,%.1f' % q for q in pts) + 'Z'
        (sp if k % 2 == 0 else dk).append(d)
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.70:.1f}" fill="none" stroke="url(#{ident}Rim)" stroke-width="{r * 0.055:.1f}"/>')
    g.append(f'<path d="{" ".join(dk)}" fill="#5d636b" stroke="#3b3f45" stroke-width="0.8"/><path d="{" ".join(sp)}" fill="url(#{ident}Rim)" stroke="#6d737a" stroke-width="0.8"/>')
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.18:.1f}" fill="#4a4f56" stroke="#2b2e33"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.09:.1f}" fill="url(#{ident}Rim)"/>')
    for k in range(5):
        a = math.radians(k * 72 - 54); g.append(f'<circle cx="{cx + math.cos(a) * r * 0.135:.1f}" cy="{cy + math.sin(a) * r * 0.135:.1f}" r="{r * 0.017:.1f}" fill="#202226"/>')

# ---------------- side view ----------------
def side(v, ident='side', paint=PAINT, hi=PAINT_HI, lo=PAINT_LO, detail=True):
    g = []
    top = [(0.0, 0.50), (0.03, 0.64), (0.10, 0.72), (0.50, 0.80), (1.00, 0.885), (1.36, 0.945), (1.70, 1.17), (2.00, 1.37), (2.55, 1.448), (3.05, 1.435),
           (3.40, 1.33), (3.78, 1.075), (4.20, 1.045), (4.58, 1.025), (4.665, 1.015)]
    tail = [(4.665, 1.015), (4.69, 0.96), (4.70, 0.80), (4.695, 0.55), (4.67, 0.36), (4.58, 0.26)]
    rarch = arc(RX, R, 0.395, 4, 176); farch = arc(FX, R, 0.395, 4, 176)
    body = v.path(('s', top), ('s', tail), ('l', [(RX + 0.42, 0.25)]), ('s', rarch), ('l', [(FX + 0.42, 0.24)]), ('s', farch),
                  ('l', [(0.50, 0.235), (0.36, 0.22)]), ('s', [(0.36, 0.22), (0.12, 0.24), (0.03, 0.34), (0.0, 0.50)]))
    gid = ident + 'G'
    g.append(f'''<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.34" stop-color="{paint}"/><stop offset="0.46" stop-color="{hi}"/><stop offset="0.50" stop-color="{paint}"/><stop offset="0.78" stop-color="{lo}"/><stop offset="1" stop-color="{lo}"/></linearGradient>
    <linearGradient id="{ident}Gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a4654"/><stop offset="0.45" stop-color="#151b22"/><stop offset="0.55" stop-color="#26303b"/><stop offset="1" stop-color="#0d1116"/></linearGradient>
    <linearGradient id="{ident}Lo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.28"/></linearGradient>
    <radialGradient id="{ident}Rim" cx="0.45" cy="0.4" r="0.7"><stop offset="0" stop-color="#f2f4f6"/><stop offset="0.6" stop-color="#bfc4ca"/><stop offset="1" stop-color="#80868d"/></radialGradient></defs>''')
    g.append(f'<path d="{body}" fill="url(#{gid})" stroke="{LINE}" stroke-width="2.2"/>')
    # lower body below the feature line darkens (surface turns under)
    g.append(f'<path d="{v.path(("s", [(0.45, 0.70), (1.6, 0.735), (3.0, 0.765), (4.66, 0.80)]), ("l", [(4.67, 0.36), (4.58, 0.26)]), ("l", [(0.36, 0.22), (0.03, 0.34)]))}" fill="url(#{ident}Lo)"/>')
    # black sill blade and bumper lowers
    g.append(f'<path d="{v.path(("l", [(1.36, 0.245), (3.30, 0.25), (3.30, 0.30)]), ("s", [(3.30, 0.30), (2.3, 0.315), (1.36, 0.30)]))}" fill="#1b1c1f"/>')
    g.append(f'<path d="{v.path(("s", [(0.03, 0.34), (0.12, 0.24), (0.36, 0.22)]), ("l", [(0.50, 0.235), (0.48, 0.28)]), ("s", [(0.48, 0.28), (0.20, 0.29), (0.07, 0.36)]))}" fill="#1b1c1f"/>')
    g.append(f'<path d="{v.path(("s", [(4.67, 0.36), (4.58, 0.26), (4.20, 0.25)]), ("l", [(4.17, 0.30)]), ("s", [(4.17, 0.30), (4.50, 0.30), (4.68, 0.40)]))}" fill="#1b1c1f"/>')
    for ax in (FX, RX):
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.395, 4, 176)), ("s", arc(ax, R, 0.368, 176, 4)))}" fill="#17181b"/>')
        g.append(f'<path d="{v.path(("s", arc(ax, R, 0.370, 4, 176)))}" fill="#0b0c0e"/>')
    # six-light glasshouse
    dlo = [(1.42, 0.985), (1.75, 1.18), (2.03, 1.355), (2.55, 1.408), (3.02, 1.395), (3.33, 1.30), (3.62, 1.10)]
    belt = [(3.62, 1.10), (3.30, 1.075), (2.4, 1.040), (1.42, 0.985)]
    g.append(f'<path d="{v.path(("s", dlo), ("s", belt))}" fill="url(#{ident}Gl)" stroke="#0a0c0f" stroke-width="3"/>')
    g.append(f'<path d="{v.path(("l", [(2.36, 1.408), (2.46, 1.408), (2.47, 1.043), (2.37, 1.040)]))}" fill="#08090b"/>')            # B-pillar
    g.append(f'<path d="{v.path(("l", [(3.12, 1.372), (3.18, 1.36), (3.16, 1.074), (3.10, 1.072)]))}" fill="#08090b"/>')             # quarter-light divider
    g.append(f'<path d="{v.path(("l", [(1.44, 0.99), (1.76, 1.19), (1.80, 1.17), (1.56, 1.01)]))}" fill="#08090b" opacity="0.9"/>')   # A-pillar shadow
    if detail:   # satin chrome DLO surround
        g.append(f'<path d="{v.path(("s", [(1.80, 1.215), (2.05, 1.375), (2.55, 1.428), (3.03, 1.414), (3.35, 1.315), (3.66, 1.10)]), ("s", [(3.66, 1.10), (3.30, 1.075), (2.4, 1.040), (1.42, 0.985)]), close=False)}" fill="none" stroke="{CHROME}" stroke-width="2.6" stroke-linecap="round"/>')
    g.append(f'<path d="{v.path(("l", [(1.95, 1.30), (2.30, 1.39), (2.08, 1.14), (1.80, 1.10)]))}" fill="#9fb4c8" opacity="0.18"/>')
    g.append(f'<path d="{v.path(("l", [(2.62, 1.39), (2.92, 1.39), (2.75, 1.13), (2.52, 1.10)]))}" fill="#9fb4c8" opacity="0.12"/>')
    # rear screen seen edge-on + boot lip spoiler
    g.append(f'<path d="{v.path(("s", [(3.08, 1.43), (3.40, 1.33), (3.76, 1.08)]), ("l", [(3.70, 1.075), (3.33, 1.32)]))}" fill="#0c0f13"/>')
    g.append(f'<path d="{v.path(("s", [(4.42, 1.035), (4.60, 1.045), (4.68, 1.035)]), ("l", [(4.668, 1.012), (4.45, 1.022)]))}" fill="#101114"/>')
    g.append(f'<path d="{v.path(("s", [(2.80, 1.442), (2.90, 1.495), (2.95, 1.497)]), ("l", [(2.97, 1.440)]))}" fill="#101114"/>')       # shark fin
    if detail:
        sl = lambda pts, w=1.6, c=LINE: g.append(f'<path d="{v.path(("s", pts), close=False)}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>')
        sl([(1.37, 0.98), (1.39, 0.70), (1.40, 0.42), (1.42, 0.30)])                     # front door leading edge
        sl([(2.42, 1.042), (2.43, 0.70), (2.44, 0.31)])                                  # B line
        sl([(3.45, 1.085), (3.42, 0.85), (3.33, 0.70)]); sl(arc(RX, 0.33, 0.45, 132, 172, 6))
        sl([(1.42, 0.30), (2.4, 0.31), (3.33, 0.315)])
        sl([(0.16, 0.76), (0.40, 0.66), (0.50, 0.52), (0.52, 0.42)])                     # bumper / wing seam
        sl([(4.69, 0.80), (4.38, 0.785), (4.22, 0.68), (4.20, 0.52)])                    # rear bumper / quarter seam
        sl([(0.10, 0.72), (0.70, 0.83), (1.36, 0.94)], 1.2, '#2a3d55')                   # bonnet shut line
        sl([(3.86, 1.072), (4.30, 1.05), (4.62, 1.03)], 1.2, '#2a3d55')                   # boot lid shut line
        sl([(4.62, 1.03), (4.66, 0.86)], 1.2, '#2a3d55')
        # crisp feature line through the handles + lower sculpt
        g.append(f'<path d="{v.path(("s", [(0.50, 0.80), (1.6, 0.835), (2.8, 0.865), (3.9, 0.895), (4.68, 0.905)]), close=False)}" fill="none" stroke="#dbe8f6" stroke-width="2.4" opacity="0.7"/>')
        g.append(f'<path d="{v.path(("s", [(0.55, 0.785), (1.6, 0.82), (2.8, 0.85), (3.9, 0.88), (4.68, 0.89)]), close=False)}" fill="none" stroke="{LINE}" stroke-width="1.6" opacity="0.6"/>')
        g.append(f'<path d="{v.path(("s", [(1.45, 0.42), (2.4, 0.445), (3.30, 0.47)]), close=False)}" fill="none" stroke="#9fb6cf" stroke-width="1.6" opacity="0.45"/>')
        # slim headlamp wrapping into the wing
        g.append(f'<path d="{v.path(("s", [(0.05, 0.705), (0.30, 0.75), (0.66, 0.80)]), ("s", [(0.66, 0.80), (0.55, 0.765), (0.28, 0.705), (0.045, 0.665)]))}" fill="#1f252c" stroke="#0b0d10" stroke-width="1.5"/>')
        g.append(f'<path d="{v.path(("s", [(0.07, 0.698), (0.34, 0.742), (0.62, 0.79)]), close=False)}" fill="none" stroke="#f3f7ff" stroke-width="2.6" stroke-linecap="round"/>')
        g.append(f'<path d="{v.path(("l", [(0.03, 0.44), (0.12, 0.43), (0.12, 0.38), (0.03, 0.39)]))}" fill="#e7ecf2" opacity="0.9"/>')   # lower DRL slit
        g.append(f'<path d="{v.path(("l", [(0.96, 0.835), (1.06, 0.848), (1.06, 0.833), (0.96, 0.82)]))}" fill="#e3922f"/>')                 # repeater
        # mirror on the door, flush handles, fuel flap
        g.append(f'<path d="{v.path(("s", [(1.48, 0.995), (1.45, 1.05), (1.52, 1.11), (1.70, 1.10), (1.72, 1.04), (1.64, 1.00)]))}" fill="url(#{gid})" stroke="{LINE}" stroke-width="1.8"/>')
        g.append(f'<path d="{v.path(("l", [(1.50, 1.055), (1.69, 1.072), (1.70, 1.055), (1.51, 1.04)]))}" fill="#101114"/>')
        for hx, hz in ((2.06, 0.852), (3.12, 0.882)):
            g.append(f'<path d="{v.path(("l", [(hx, hz), (hx + 0.20, hz + 0.004), (hx + 0.20, hz - 0.018), (hx, hz - 0.022)]))}" fill="{CHROME}" stroke="#4a5058" stroke-width="1"/>')
        fx_, fz_ = v.p(3.96, 0.99); g.append(f'<rect x="{fx_:.1f}" y="{fz_:.1f}" width="{0.14 * v.sc:.1f}" height="{0.10 * v.sc:.1f}" rx="5" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
        # tail lamp wrapping round the corner
        g.append(f'<path d="{v.path(("l", [(4.695, 0.99), (4.40, 0.998), (4.36, 0.965), (4.70, 0.945)]))}" fill="#a3151b" stroke="#3a0608" stroke-width="1.4"/>')
        g.append(f'<path d="{v.path(("l", [(4.69, 0.975), (4.42, 0.982)]), close=False)}" fill="none" stroke="#ff5a4e" stroke-width="2.2" stroke-linecap="round"/>')
        g.append(f'<path d="{v.path(("l", [(4.56, 0.42), (4.68, 0.42), (4.68, 0.39), (4.56, 0.39)]))}" fill="#8b1015"/>')
    for ax in (FX, RX): tyre_wheel(v, g, ident, ax)
    return '\n'.join(g)

# ---------------- front and rear ----------------
def _shell(v, gid, half):
    m = lambda pts: [(-y, z) for y, z in reversed(pts)]
    return v.path(("s", half[:-1] + [(0.0, H)]), ("s", m(half)[1:]))

def front(v, paint=PAINT, hi=PAINT_HI, lo=PAINT_LO):
    g = []; P = lambda pts: v.path(('s', pts))
    half = [(0.0, 0.23), (0.66, 0.225), (0.89, 0.29), (0.92, 0.48), (0.915, 0.78), (0.88, 0.90), (0.78, 0.99), (0.66, 1.31), (0.54, 1.43), (0.0, H)]
    g.append(f'<defs><linearGradient id="fG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.45" stop-color="{paint}"/><stop offset="1" stop-color="{lo}"/></linearGradient></defs>')
    for s_ in (-1, 1):
        x0, y0 = v.p(s_ * 0.79 - 0.108, R * 2); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.215 * v.sc:.1f}" height="{R * 2 * v.sc:.1f}" rx="{0.05 * v.sc:.1f}" fill="#17181a"/>')
    g.append(f'<path d="{_shell(v, "fG", half)}" fill="url(#fG)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.72, 0.99), (0.61, 1.28), (0.50, 1.39), (0.0, 1.405), (-0.50, 1.39), (-0.61, 1.28), (-0.72, 0.99)]), ("s", [(-0.72, 0.99), (0.0, 0.965), (0.72, 0.99)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    g.append(f'<path d="{v.path(("l", [(-0.38, 1.33), (0.02, 1.39), (0.22, 1.39), (-0.18, 1.05), (-0.52, 1.07)]))}" fill="#9fb4c8" opacity="0.14"/>')
    g.append(f'<rect x="{v.p(-0.06, 1.39)[0]:.1f}" y="{v.p(-0.06, 1.39)[1]:.1f}" width="{0.12 * v.sc:.1f}" height="{0.07 * v.sc:.1f}" rx="3" fill="#26292e"/>')
    for s_ in (-1, 1):
        q = lambda pts: [(s_ * y, z) for y, z in pts]
        g.append(f'<path d="{P(q([(0.76, 0.98), (1.00, 0.985), (1.02, 1.07), (0.97, 1.11), (0.80, 1.09)]))}" fill="url(#fG)" stroke="{LINE}" stroke-width="1.8"/>')
        # slim headlamp, inner end meets the grille bar
        g.append(f'<path d="{v.path(("s", q([(0.40, 0.775), (0.66, 0.785), (0.88, 0.775)])), ("s", q([(0.89, 0.735), (0.66, 0.725), (0.42, 0.735)])))}" fill="#1f252c" stroke="#0b0d10" stroke-width="1.5"/>')
        g.append(f'<path d="{v.path(("s", q([(0.42, 0.768), (0.66, 0.778), (0.87, 0.768)])), close=False)}" fill="none" stroke="#f3f7ff" stroke-width="3" stroke-linecap="round"/>')
        for yy in (0.56, 0.66, 0.76):
            c = v.p(s_ * yy, 0.746); g.append(f'<rect x="{c[0] - 0.035 * v.sc:.1f}" y="{c[1] - 0.012 * v.sc:.1f}" width="{0.07 * v.sc:.1f}" height="{0.024 * v.sc:.1f}" rx="3" fill="#cfd7e0"/>')
        # vertical corner intakes with DRL slit
        g.append(f'<path d="{v.path(("l", q([(0.70, 0.56), (0.84, 0.58), (0.86, 0.33), (0.74, 0.32)])))}" fill="#151619"/>')
        g.append(f'<path d="{v.path(("l", q([(0.80, 0.55), (0.83, 0.555), (0.845, 0.36), (0.815, 0.355)])))}" fill="#e7ecf2"/>')
    # thin lit grille bar between the lamps, wide upper grille with horizontal slats, lower intake
    g.append(f'<path d="{P([(-0.42, 0.755), (0.0, 0.765), (0.42, 0.755)])}" fill="none" stroke="#e7ecf2" stroke-width="3"/>')
    g.append(f'<path d="{v.path(("s", [(-0.52, 0.715), (0.0, 0.725), (0.52, 0.715)]), ("s", [(0.46, 0.58), (0.0, 0.575), (-0.46, 0.58)]))}" fill="#121316" stroke="#08090b" stroke-width="2"/>')
    for z in (0.69, 0.66, 0.63, 0.60):
        g.append(f'<path d="{P([(-0.48, z), (0.0, z + 0.006), (0.48, z)])}" fill="none" stroke="#565b62" stroke-width="2"/>')
    c = v.p(0, 0.65); g.append(f'<path d="M{c[0] - 14:.1f},{c[1] - 8:.1f} L{c[0]:.1f},{c[1] + 9:.1f} L{c[0] + 14:.1f},{c[1] - 8:.1f}" fill="none" stroke="#e4e7eb" stroke-width="3.4" stroke-linejoin="round"/>')   # V badge
    g.append(f'<path d="{v.path(("s", [(-0.62, 0.50), (0.0, 0.51), (0.62, 0.50)]), ("s", [(0.58, 0.29), (0.0, 0.28), (-0.58, 0.29)]))}" fill="#141518" stroke="#08090b" stroke-width="2"/>')
    for k in range(-5, 6):
        x0 = v.p(k * 0.10, 0.48)[0]; y0, y1 = v.p(0, 0.48)[1], v.p(0, 0.31)[1]
        g.append(f'<path d="M{x0:.1f},{y0:.1f} L{x0:.1f},{y1:.1f}" stroke="#25272b" stroke-width="2"/>')
    x0, y0 = v.p(-0.26, 0.47); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.52 * v.sc:.1f}" height="{0.11 * v.sc:.1f}" rx="3" fill="#f2f0ea" stroke="#333"/><text x="{v.p(0, 0.40)[0]:.1f}" y="{v.p(0, 0.40)[1]:.1f}" font-size="17" text-anchor="middle" font-family="Inter" font-weight="700" fill="#222">AU · V3LA</text>')
    g.append(f'<path d="{P([(-0.70, 0.88), (0.0, 0.905), (0.70, 0.88)])}" fill="none" stroke="#2a3d55" stroke-width="1.4"/>')   # bonnet shut line
    return '\n'.join(g)

def rear(v, paint=PAINT, hi=PAINT_HI, lo=PAINT_LO):
    g = []; P = lambda pts: v.path(('s', pts))
    half = [(0.0, 0.24), (0.66, 0.235), (0.89, 0.29), (0.92, 0.48), (0.915, 0.90), (0.88, 1.00), (0.78, 1.06), (0.64, 1.31), (0.54, 1.43), (0.0, H)]
    g.append(f'<defs><linearGradient id="rG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hi}"/><stop offset="0.45" stop-color="{paint}"/><stop offset="1" stop-color="{lo}"/></linearGradient></defs>')
    for s_ in (-1, 1):
        x0, y0 = v.p(s_ * 0.79 - 0.108, R * 2); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.215 * v.sc:.1f}" height="{R * 2 * v.sc:.1f}" rx="{0.05 * v.sc:.1f}" fill="#17181a"/>')
    g.append(f'<path d="{_shell(v, "rG", half)}" fill="url(#rG)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(0.66, 1.09), (0.56, 1.30), (0.46, 1.37), (0.0, 1.38), (-0.46, 1.37), (-0.56, 1.30), (-0.66, 1.09)]), ("s", [(-0.66, 1.09), (0.0, 1.075), (0.66, 1.09)]))}" fill="#151b22" stroke="#08090b" stroke-width="3"/>')
    g.append(f'<path d="{v.path(("s", [(-0.70, 1.055), (0.0, 1.07), (0.70, 1.055)]), ("s", [(0.70, 1.035), (0.0, 1.045), (-0.70, 1.035)]))}" fill="#101114"/>')   # lip spoiler
    x0, y0 = v.p(-0.06, 1.395); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.12 * v.sc:.1f}" height="{0.016 * v.sc:.1f}" fill="#b0131a"/>')
    # full-width light bar
    g.append(f'<path d="{v.path(("s", [(-0.90, 0.985), (0.0, 1.0), (0.90, 0.985)]), ("s", [(0.91, 0.935), (0.0, 0.95), (-0.91, 0.935)]))}" fill="#7d1015" stroke="#3a0608" stroke-width="1.4"/>')
    g.append(f'<path d="{P([(-0.88, 0.962), (0.0, 0.977), (0.88, 0.962)])}" fill="none" stroke="#ff5a4e" stroke-width="2.4"/>')
    for s_ in (-1, 1):
        q = lambda pts: [(s_ * y, z) for y, z in pts]
        g.append(f'<path d="{v.path(("s", q([(0.60, 0.99), (0.78, 0.988), (0.905, 0.98)])), ("s", q([(0.91, 0.875), (0.78, 0.878), (0.62, 0.885)])))}" fill="#a3151b" stroke="#3a0608" stroke-width="1.5"/>')
        for zz in (0.955, 0.925, 0.895):
            g.append(f'<path d="{v.path(("l", q([(0.64, zz), (0.89, zz - 0.004)])), close=False)}" stroke="#ff6a5e" stroke-width="2" stroke-linecap="round"/>')
        g.append(f'<path d="{v.path(("l", q([(0.70, 0.43), (0.86, 0.45), (0.86, 0.42), (0.70, 0.40)])))}" fill="#8b1015"/>')
        g.append(f'<path d="{v.path(("l", q([(0.50, 0.33), (0.66, 0.33), (0.66, 0.30), (0.50, 0.30)])))}" fill="#e8ecf0"/>')    # reverse lamp in bumper
    g.append(f'<text x="{v.p(0, 0.86)[0]:.1f}" y="{v.p(0, 0.86)[1]:.1f}" font-size="15" text-anchor="middle" font-family="Inter" font-weight="800" letter-spacing="8" fill="#d9dde2">VELA</text>')
    g.append(f'<path d="{v.path(("s", [(-0.62, 1.02), (0.0, 1.03), (0.62, 1.02)]), ("l", [(0.60, 0.80)]), ("s", [(0.60, 0.80), (0.0, 0.795), (-0.60, 0.80)]))}" fill="none" stroke="#2a3d55" stroke-width="1.5"/>')   # boot lid
    x0, y0 = v.p(-0.26, 0.66); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.52 * v.sc:.1f}" height="{0.12 * v.sc:.1f}" rx="3" fill="#f2f0ea" stroke="#333"/><text x="{v.p(0, 0.585)[0]:.1f}" y="{v.p(0, 0.585)[1]:.1f}" font-size="17" text-anchor="middle" font-family="Inter" font-weight="700" fill="#222">AU · V3LA</text>')
    g.append(f'<path d="{v.path(("s", [(-0.84, 0.40), (0.0, 0.41), (0.84, 0.40)]), ("l", [(0.86, 0.28), (-0.86, 0.28)]))}" fill="#1b1c1f"/>')
    for s_ in (-1, 1):   # twin trapezoid tail-pipe trims
        x0, y0 = v.p(s_ * 0.52 - 0.11, 0.37); g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{0.22 * v.sc:.1f}" height="{0.06 * v.sc:.1f}" rx="5" fill="#0a0b0d" stroke="{CHROME}" stroke-width="2.4"/>')
    return '\n'.join(g)

def top(v, paint=PAINT, hi=PAINT_HI):
    g = []
    half = [(0.0, 0.0), (0.0, 0.64), (0.07, 0.82), (0.34, 0.905), (0.9, 0.92), (2.6, 0.92), (3.9, 0.915), (4.45, 0.87), (4.66, 0.76), (4.70, 0.0)]
    m = [(x, -y) for x, y in reversed(half)]
    g.append(f'<defs><linearGradient id="tG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAINT_LO}"/><stop offset="0.3" stop-color="{paint}"/><stop offset="0.5" stop-color="{hi}"/><stop offset="0.7" stop-color="{paint}"/><stop offset="1" stop-color="{PAINT_LO}"/></linearGradient></defs>')
    g.append(f'<path d="{v.path(("s", half[1:-1]), ("s", m[1:-1]))}" fill="url(#tG)" stroke="{LINE}" stroke-width="2.2"/>')
    g.append(f'<path d="{v.path(("s", [(1.38, 0.68), (2.05, 0.60), (3.10, 0.60), (3.78, 0.62)]), ("l", [(3.78, -0.62)]), ("s", [(3.78, -0.62), (3.10, -0.60), (2.05, -0.60), (1.38, -0.68)]), ("s", [(1.38, -0.68), (1.33, 0.0), (1.38, 0.68)]))}" fill="#151b22"/>')
    g.append(f'<path d="{v.path(("s", [(2.06, 0.56), (2.6, 0.585), (3.12, 0.565)]), ("l", [(3.12, -0.565)]), ("s", [(3.12, -0.565), (2.6, -0.585), (2.06, -0.56)]))}" fill="url(#tG)" stroke="{LINE}" stroke-width="1.4"/>')
    g.append(f'<path d="{v.path(("l", [(4.42, 0.78), (4.62, 0.70), (4.62, -0.70), (4.42, -0.78)]))}" fill="#101114" opacity="0.85"/>')
    g.append(f'<path d="{v.path(("l", [(3.86, 0.80), (4.62, 0.74)]), close=False)}" stroke="#2a3d55" stroke-width="1.4"/><path d="{v.path(("l", [(3.86, -0.80), (4.62, -0.74)]), close=False)}" stroke="#2a3d55" stroke-width="1.4"/>')
    for s_ in (-1, 1):
        g.append(f'<path d="{v.path(("l", [(1.50, s_ * 0.92), (1.54, s_ * 1.02), (1.72, s_ * 1.02), (1.70, s_ * 0.92)]))}" fill="{paint}" stroke="{LINE}" stroke-width="1.4"/>')
        g.append(f'<path d="{v.path(("s", [(0.06, s_ * 0.64), (0.14, s_ * 0.83), (0.62, s_ * 0.90)]), close=False)}" fill="none" stroke="#f3f7ff" stroke-width="3"/>')
        g.append(f'<path d="{v.path(("s", [(1.34, s_ * 0.64), (0.70, s_ * 0.62), (0.10, s_ * 0.42)]), close=False)}" fill="none" stroke="#2a3d55" stroke-width="1.4"/>')
        g.append(f'<path d="{v.path(("s", [(0.4, s_ * 0.30), (0.9, s_ * 0.33), (1.30, s_ * 0.34)]), close=False)}" fill="none" stroke="#9fb6cf" stroke-width="1.4" opacity="0.6"/>')   # bonnet creases
    g.append(f'<path d="{v.path(("l", [(2.80, 0.0), (2.96, 0.0)]), close=False)}" stroke="#101114" stroke-width="7" stroke-linecap="round"/>')
    return '\n'.join(g)

def dims_side(v):
    g = []; y = v.p(0, -0.12)[1]; a, b = v.p(0, 0)[0], v.p(L, 0)[0]
    ln = lambda x1, y1, x2, y2: g.append(f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke="#7d786f" stroke-width="1.2"/>')
    ln(a, y, b, y); ln(a, y - 8, a, y + 8); ln(b, y - 8, b, y + 8)
    g.append(f'<text x="{(a + b) / 2:.1f}" y="{y + 26:.1f}" class="dim">4,700 mm</text>')
    y2 = v.p(0, -0.30)[1]; fa, ra = v.p(FX, 0)[0], v.p(RX, 0)[0]; ln(fa, y2, ra, y2); ln(fa, y2 - 6, fa, y2 + 6); ln(ra, y2 - 6, ra, y2 + 6)
    g.append(f'<text x="{(fa + ra) / 2:.1f}" y="{y2 + 26:.1f}" class="dim">wheelbase 2,800</text>')
    x = v.p(L + 0.16, 0)[0]; t, bt = v.p(0, H)[1], v.p(0, 0)[1]; ln(x, t, x, bt); ln(x - 8, t, x + 8, t); ln(x - 8, bt, x + 8, bt)
    g.append(f'<text x="{x + 12:.1f}" y="{(t + bt) / 2:.1f}" class="dim" text-anchor="start">1,450</text>')
    gl = v.p(-0.15, 0); gr = v.p(L + 0.15, 0); g.append(f'<path d="M{gl[0]:.1f},{gl[1]:.1f} L{gr[0]:.1f},{gr[1]:.1f}" stroke="#4a4740" stroke-width="2"/>')
    return '\n'.join(g)

def silhouette(v, kind):
    if kind != 'saloon': return mira_silhouette(v, kind)
    top_ = [(0.0, 0.50), (0.10, 0.72), (1.00, 0.885), (1.36, 0.945), (2.00, 1.37), (2.55, 1.448), (3.05, 1.435), (3.40, 1.33), (3.78, 1.075), (4.58, 1.025), (4.69, 0.96), (4.70, 0.55), (4.58, 0.26)]
    d = v.path(('s', top_), ('l', [(RX + 0.42, 0.25)]), ('s', arc(RX, 0.33, 0.41, 8, 172)), ('l', [(FX + 0.42, 0.24)]), ('s', arc(FX, 0.33, 0.41, 8, 172)), ('l', [(0.10, 0.24), (0, 0.50)]))
    out = f'<path d="{d}" fill="#3a3f46" stroke="#5a6069" stroke-width="1.5"/>'
    for a in (FX, RX):
        c = v.p(a, R); out += f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{R * v.sc:.1f}" fill="#1a1b1d"/><circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{R * v.sc * 0.6:.1f}" fill="#5c626a"/>'
    return out

PALETTE = [('Slate blue', '#3f5f82', '#7d9dbf', '#1f3249'), ('Burgundy', '#6e1f2b', '#a1475a', '#3b0f17'), ('Moon silver', '#a9afb6', '#e1e5ea', '#6a7077'),
           ('Midnight', '#1d2129', '#4a5160', '#0b0d11'), ('Sandstone', '#b9a07a', '#dbc7a3', '#7a6545'), ('Pine green', '#2e5444', '#5e8a77', '#16291f')]

def build(out_html):
    Wd, Hd = 3000, 1860
    S0 = 228
    sv = View(90, 690, S0); body = [side(sv), dims_side(sv)]
    fv = View(1690, 690, S0); body.append(front(fv)); rv = View(2550, 690, S0); body.append(rear(rv))
    for vv, lab in ((fv, 'FRONT'), (rv, 'REAR')):
        body.append(f'<text x="{vv.ox:.0f}" y="{vv.oy + 50:.0f}" class="vl" text-anchor="middle">{lab}</text>')
    body.append(f'<text x="{sv.ox:.0f}" y="{sv.oy + 130:.0f}" class="vl">SIDE (LEFT)</text>')
    w = lambda x, z: tuple(map(int, sv.p(x, z)))
    body += [callout(*w(0.35, 0.74), 120, 236, 'Slim headlamps joined by a lit grille bar'),
             callout(*w(2.2, 1.40), 640, 236, 'Six-light glasshouse, satin chrome surround'),
             callout(*w(3.13, 1.25), 1000, 300, 'Quarter window behind the rear door'),
             callout(*w(4.55, 1.04), 1180, 360, 'Short boot deck with lip spoiler'),
             callout(*w(2.2, 0.85), 720, 860, 'Crisp feature line through flush chrome handles'),
             callout(*w(RX + 0.14, 0.42), 1230, 860, '17" ten-spoke two-tone alloy')]
    tv = View(110, 1180, 150); body.append(top(tv)); body.append(f'<text x="{tv.ox:.0f}" y="{tv.oy + 175:.0f}" class="vl">TOP</text>')
    for i, (n, c, hi, lo) in enumerate(PALETTE):
        vv = View(900 + (i % 3) * 330, 1120 + (i // 3) * 230, 62)
        body.append(side(vv, 'p%d' % i, c, hi, lo, detail=False)); body.append(f'<text x="{vv.ox + 146:.0f}" y="{vv.oy + 34:.0f}" class="sub" text-anchor="middle">{n}</text>')
    body.append('<text x="900" y="985" class="lbl">TRAFFIC PAINTS (RANDOM PER CAR)</text>')
    zooms = [((0.0, 0.55, 0.75, 0.88), 'Headlamp'), ((4.10, 0.86, 4.72, 1.08), 'Tail lamp'), ((RX - 0.38, -0.02, RX + 0.38, 0.70), 'Wheel')]
    zx = 1960; body.append(f'<text x="{zx}" y="985" class="lbl">DETAILS</text>')
    for k, ((x0, z0, x1, z1), lab) in enumerate(zooms):
        a = sv.p(x0, z1); b = sv.p(x1, z0); ww, hh = b[0] - a[0], b[1] - a[1]
        body.append(f'<svg x="{zx + k * 330}" y="1005" width="300" height="230" viewBox="{a[0]:.1f} {a[1]:.1f} {ww:.1f} {hh:.1f}" preserveAspectRatio="xMidYMid meet"><rect x="{a[0] - 50}" y="{a[1] - 50}" width="{ww + 100}" height="{hh + 100}" fill="#1e2227"/><use href="#sideAll"/></svg>')
        body.append(f'<text x="{zx + k * 330 + 150}" y="1262" class="sub" text-anchor="middle">{lab}</text>')
    for i, (kind, name, note) in enumerate((('hatch', '01 · Mira', 'Compact hatchback'), ('saloon', '02 · Vela', 'Four-door family saloon'), ('suv', '03 · SUV', 'Compact crossover'), ('van', '04 · Van', 'Delivery van'), ('saloon', '05 · Taxi', 'Vela in taxi livery'))):
        vv = View(1960 + (i % 3) * 330, 1440 + (i // 3) * 200, 50)
        body.append(silhouette(vv, kind))
        if i == 0: body.append(f'<text x="{vv.ox + 250:.0f}" y="{vv.oy - 105:.0f}" class="sub" text-anchor="end" style="fill:#7fae7a">✓ in game</text>')
        if i == 1: body.append(f'<rect x="{vv.ox - 12}" y="{vv.oy - 130}" width="300" height="175" rx="8" fill="none" stroke="#c9a45c" stroke-width="2"/>')
        body.append(f'<text x="{vv.ox:.0f}" y="{vv.oy + 34:.0f}" class="cap2">{name}</text><text x="{vv.ox + 100:.0f}" y="{vv.oy + 34:.0f}" class="sub">{note}</text>')
    body.append('<text x="1960" y="1300" class="lbl">THE TRAFFIC FAMILY (ONE SHEET EACH)</text>')
    html = f'''<html><head><meta charset="utf-8"><style>body{{margin:0;background:#16191d;font-family:Inter}}
.dim{{font-size:17px;fill:#a8a39a;text-anchor:middle;letter-spacing:1px}}.vl{{font-size:14px;fill:#8d887f;letter-spacing:3px;font-weight:700}}
.co{{font-size:16px;fill:#e9e6df}}.sub{{font-size:15px;fill:#a8a39a}}.lbl{{font-size:14px;fill:#8d887f;letter-spacing:3px;font-weight:700}}.cap2{{font-size:16px;fill:#e9e6df;font-weight:800}}
.h b{{font-size:44px;letter-spacing:2px;color:#e9e6df}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.spec{{position:absolute;left:60px;top:1440px;width:1800px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:34px;color:#a8a39a;font-size:16px;line-height:1.55}}.spec b{{display:block;font-size:14px;letter-spacing:3px;color:#8d887f;margin-bottom:8px}}
</style></head><body style="width:{Wd}px;height:{Hd}px;position:relative">
<div class="h" style="padding:46px 60px 0"><i class="tag">TRAFFIC 02</i><b>VELA — FAMILY SALOON</b><span>Design sheet for approval · the commuter and family car on Aurelia's roads · base for the 05 taxi · original design, no real make · modelled in Blender after approval</span></div>
<svg width="{Wd}" height="{Hd}" style="position:absolute;left:0;top:0"><defs><g id="sideAll">{side(View(90, 690, S0), 'z')}</g></defs>{"".join(body)}</svg>
<div class="spec">
<div><b>DIMENSIONS</b>4,700 × 1,840 × 1,450 mm · wheelbase 2,800 · 17" wheels, 215/55 tyres · 4 doors + boot · front-wheel drive<br>Calm, grown-up three-box car: long bonnet, cab set back, roof falling to a short notched boot. Longer and lower-shouldered than the Mira, flat sides with one sharp line instead of soft sculpt.</div>
<div><b>MODEL</b>Same pipeline as the Mira: field-sculpted body with real panel gaps and thickness · separate tinted, see-through glass with chrome surround · simple interior (seats, dash, wheel) · lamps as separate parts that glow at night: headlamps, grille bar, full-width tail bar, brake, indicators, reverse.<br>~30k triangles close up · 8k mid · 1.5k far.</div>
<div><b>MATERIALS</b>Metallic paint with clear coat in six traffic colours · satin chrome window line and handles · textured black plastic on bumpers, sills and arch liners · gloss black pillars, spoiler and grille · two-tone machined/graphite alloys · rubber tyres with tread · red, amber and clear lenses.</div>
</div></body></html>'''
    open(out_html, 'w').write(html)

if __name__ == '__main__':
    build(sys.argv[1])
