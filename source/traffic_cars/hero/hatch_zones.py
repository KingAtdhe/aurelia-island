"""Zones on the Hatch body (traced from the reference): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from hatch_sdf import crs, sstep, FS, RS, R, L

SQ = 1 / np.sqrt(2)
DLO = closed([(1.12, 1.022), (1.37, 1.174), (1.66, 1.373), (2.0, 1.425), (2.32, 1.434), (3.0, 1.43), (3.24, 1.418), (3.49, 1.205)],
             [(3.49, 1.205), (3.32, 1.052), (2.4, 1.040), (1.12, 1.022)])
BPIL = [(2.30, 1.46), (2.40, 1.46), (2.41, 1.03), (2.31, 1.03)]
QDIV = [(3.06, 1.44), (3.13, 1.44), (3.14, 1.05), (3.07, 1.05)]
WS = closed([(1.07, -0.001), (1.075, 0.52), (1.11, 0.64), (1.18, 0.70)], [(1.18, 0.70), (1.62, 0.60), (1.69, 0.52), (1.71, -0.001)])
RG = closed([(0.0, 1.04), (0.58, 1.05), (0.63, 1.07)], [(0.63, 1.07), (0.58, 1.30), (0.50, 1.36), (0.0, 1.37)])
HL = closed([(0.12, 0.855), (0.45, 0.858), (0.80, 0.862)], [(0.80, 0.862), (0.76, 0.810), (0.45, 0.796), (0.12, 0.800)])
HL_DRL = [(0.13, 0.845), (0.45, 0.848), (0.79, 0.850)]
LOWER = closed([(-0.64, 0.400), (-0.3, 0.388), (0.0, 0.385), (0.3, 0.388), (0.64, 0.400)], [(0.60, 0.272), (0.0, 0.265), (-0.60, 0.272)])
TL = closed([(0.25, 1.030), (0.5, 1.032), (0.78, 1.010)], [(0.78, 1.010), (0.76, 0.985), (0.5, 0.990), (0.25, 0.995)])
TL_BARS = [[(0.27, 1.012), (0.5, 1.014), (0.75, 1.000)]]

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.60): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    uf = lambda s, y: (sym_y(y) + s) * SQ
    ur = lambda s, y: (sym_y(y) + L - s) * SQ
    Z.append(('Clad', lambda s, y, z: z - (0.235 + 0.07 * sstep(3.85, 4.05, s) + 0.02 * sstep(0.30, 0.10, s)), 0.0))
    Z.append(('Liner', lambda s, y, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2)) - 0.400, 0.0))
    Z.append(('Trim', lambda s, y, z: side(DLO, s, y, z) - 0.018, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 0.95) & (s < 1.8))),
                                                   mask(poly_sd(RG, sym_y(y), z), (s > 3.6) & (s < 4.12))), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: np.minimum(side(BPIL, s, y, z), side(QDIV, s, y, z)), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HL, uf(s, y), z), s < 0.7), 0.005))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.30), 0.02))
    Z.append(('Tail', lambda s, y, z: mask(poly_sd(TL, ur(s, y), z), s > 3.75), 0.005))
    return Z

GROUPS = [(('Lamp',), 0.006, 'Lamp'), (('Tail',), 0.006, 'Tail'), (('Intake',), 0.02, 'Intake')]
ARC = lambda a0, a1, r: [(RS + r * np.cos(a), R + r * np.sin(a)) for a in np.radians(np.linspace(a0, a1, 9))]
GAPS = [
    ('sz', [(1.12, 1.022), (1.13, 0.70), (1.14, 0.40), (1.16, 0.25)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(2.36, 1.04), (2.37, 0.70), (2.38, 0.25)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(3.38, 1.06), (3.36, 0.85), (3.30, 0.74)] + ARC(125, 176, 0.46), lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(1.16, 0.25), (2.4, 0.25), (3.10, 0.26)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(0.25, 0.84), (0.31, 0.70), (0.34, 0.55), (0.35, 0.42)], lambda s, y, z: sym_y(y) > 0.55, 0),
    ('sz', [(4.12, 0.80), (3.98, 0.79), (3.92, 0.66), (3.92, 0.50)], lambda s, y, z: sym_y(y) > 0.55, 0),
    ('sy', [(1.06, 0.66), (0.75, 0.80), (0.45, 0.82), (0.22, 0.72), (0.14, 0.45), (0.12, 0.0)], lambda s, y, z: z > 0.80, 0),
    ('yz', [(-0.64, 0.57), (0.64, 0.57)], lambda s, y, z: s > 3.75, -1),
    ('yz', [(0.64, 1.40), (0.65, 0.57)], lambda s, y, z: s > 3.75, -1),
    ('yz', [(-0.64, 1.40), (-0.65, 0.57)], lambda s, y, z: s > 3.75, -1),
]
FUEL = (3.28, 3.40, 0.93, 1.02)
