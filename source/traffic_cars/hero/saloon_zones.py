"""Zones on the Saloon body (traced from the reference): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from saloon_sdf import crs, sstep, FS, RS, R, L

SQ = 1 / np.sqrt(2)
DLO = closed([(1.45, 1.000), (1.75, 1.170), (2.05, 1.330), (2.55, 1.390), (3.05, 1.378), (3.40, 1.295), (3.70, 1.165), (3.88, 1.088)],
             [(3.88, 1.088), (3.40, 1.058), (2.4, 1.030), (1.45, 1.000)])
BPIL = [(2.56, 1.46), (2.66, 1.46), (2.67, 1.02), (2.57, 1.02)]
QDIV = [(3.38, 1.40), (3.45, 1.40), (3.44, 1.05), (3.37, 1.05)]
WS = closed([(1.37, -0.001), (1.375, 0.50), (1.42, 0.66), (1.50, 0.725)], [(1.50, 0.725), (1.98, 0.615), (2.07, 0.53), (2.09, -0.001)])
RG = closed([(0.0, 1.105), (0.60, 1.112), (0.665, 1.130)], [(0.665, 1.130), (0.565, 1.30), (0.47, 1.365), (0.0, 1.385)])
HL = closed([(0.30, 0.742), (0.55, 0.748), (0.78, 0.755), (0.98, 0.765), (1.12, 0.782)], [(1.12, 0.782), (1.00, 0.745), (0.80, 0.712), (0.55, 0.700), (0.30, 0.696)])
HL_DRL = [(0.32, 0.736), (0.55, 0.741), (0.78, 0.748), (0.98, 0.757), (1.10, 0.773)]
LOWER = closed([(-0.66, 0.415), (-0.3, 0.405), (0.0, 0.402), (0.3, 0.405), (0.66, 0.415)], [(0.62, 0.262), (0.0, 0.255), (-0.62, 0.262)])
TL = closed([(0.44, 0.990), (0.62, 0.990), (0.78, 0.988), (0.90, 0.985)], [(0.90, 0.985), (0.88, 0.950), (0.62, 0.944), (0.44, 0.945)])
TL_BARS = [[(0.46, 0.968), (0.62, 0.968), (0.78, 0.967), (0.88, 0.967)]]

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.63): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    uf = lambda s, y: (sym_y(y) + s) * SQ
    ur = lambda s, y: (sym_y(y) + L - s) * SQ
    Z.append(('Clad', lambda s, y, z: z - (0.245 + 0.13 * sstep(4.42, 4.62, s) + 0.02 * sstep(0.40, 0.14, s)), 0.0))
    Z.append(('Liner', lambda s, y, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2)) - 0.410, 0.0))
    Z.append(('Chrome', lambda s, y, z: side(DLO, s, y, z) - 0.016, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 0.95) & (s < 2.2))),
                                                   mask(poly_sd(RG, sym_y(y), z), (s > 3.35) & (s < 4.20))), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: np.minimum(side(BPIL, s, y, z), side(QDIV, s, y, z)), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HL, uf(s, y), z), s < 0.8), 0.005))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.35), 0.02))
    Z.append(('Tail', lambda s, y, z: np.minimum(mask(poly_sd(TL, ur(s, y), z), s > 4.3), mask(np.maximum(np.abs(z - 0.967) - 0.017, sym_y(y) - 0.70), s > 4.55)), 0.005))
    return Z

GROUPS = [(('Lamp',), 0.006, 'Lamp'), (('Tail',), 0.006, 'Tail'), (('Intake',), 0.02, 'Intake')]
ARC = lambda a0, a1, r: [(RS + r * np.cos(a), R + r * np.sin(a)) for a in np.radians(np.linspace(a0, a1, 9))]
GAPS = [
    ('sz', [(1.40, 0.995), (1.41, 0.70), (1.42, 0.42), (1.44, 0.27)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(2.61, 1.033), (2.62, 0.70), (2.63, 0.27)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(3.55, 1.065), (3.52, 0.88), (3.46, 0.77)] + ARC(125, 176, 0.47), lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(1.44, 0.27), (2.6, 0.275), (3.40, 0.28)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(0.26, 0.75), (0.38, 0.66), (0.44, 0.52), (0.46, 0.40)], lambda s, y, z: sym_y(y) > 0.55, 0),
    ('sz', [(4.76, 0.84), (4.48, 0.83), (4.32, 0.72), (4.29, 0.50)], lambda s, y, z: sym_y(y) > 0.55, 0),
    ('sy', [(1.33, 0.70), (1.0, 0.79), (0.62, 0.835), (0.40, 0.82), (0.30, 0.60), (0.27, 0.30), (0.26, 0.0)], lambda s, y, z: z > 0.70, 0),
    ('sy', [(4.24, 0.0), (4.24, 0.78), (4.48, 0.80), (4.66, 0.76)], lambda s, y, z: z > 0.95, 0),
    ('yz', [(-0.66, 0.83), (0.66, 0.83)], lambda s, y, z: s > 4.5, -1),
    ('yz', [(0.66, 0.99), (0.67, 0.83)], lambda s, y, z: s > 4.5, -1),
    ('yz', [(-0.66, 0.99), (-0.67, 0.83)], lambda s, y, z: s > 4.5, -1),
]
FUEL = (4.06, 4.20, 0.90, 0.99)
