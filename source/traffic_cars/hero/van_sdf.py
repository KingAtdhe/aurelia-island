"""Van (traffic car 06): panel van body as a signed distance field, traced from Saba's reference sheet (tcars/ref/van.jpg).
Sheet coordinates: s from the front bumper (0) to the rear bumper (4.80), z up, y left. Side view scaled 0.0064 m/px."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep
from scipy import ndimage as _nd

L, R, FS, RS = 4.80, 0.40, 0.82, 3.86
C0 = L / 2
H = 0.014
S0, S1, Y0, Z0, Z1 = -0.06, 4.86, 1.08, 0.30, 2.66
NOSEB = [(0.40, 0.43), (0.06, 0.43), (0.012, 0.46), (0.0, 0.52)]
TOP = [(0.0, 0.52), (0.0, 0.80), (0.03, 0.835), (0.055, 0.88), (0.062, 1.00), (0.072, 1.20), (0.10, 1.33), (0.18, 1.40), (0.40, 1.48), (0.62, 1.565),
       (0.79, 1.645), (0.85, 1.72), (1.10, 2.03), (1.35, 2.36), (1.46, 2.49), (1.56, 2.55), (1.72, 2.572), (2.5, 2.576), (4.45, 2.576), (4.58, 2.562), (4.66, 2.52)]
TAIL = [(4.66, 2.52), (4.70, 2.44), (4.715, 2.30), (4.72, 1.50), (4.72, 0.86), (4.76, 0.825), (4.80, 0.79), (4.80, 0.50), (4.78, 0.45), (4.72, 0.43)]
PLAN = [(0.0, 0.0), (0.004, 0.50), (0.02, 0.76), (0.07, 0.90), (0.16, 0.965), (0.32, 0.995), (0.7, 1.0), (4.6, 1.0), (4.70, 0.985), (4.76, 0.95),
        (4.79, 0.85), (4.80, 0.0)]
BELT = 1.62

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(4.72, 0.43), (0.40, 0.43)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 2.8); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.12, 1.12)
    FS2 = (_nd.gaussian_filter(FS2[0], 4.0),) + FS2[1:]; FP = (_nd.gaussian_filter(FP[0], 4.0),) + FP[1:]
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    zz = z[None, :]
    taper = (np.maximum(0, zz - BELT) * 0.11 + 0.9 * np.maximum(0, zz - 2.30) ** 2 + np.maximum(0, 0.60 - zz) * 0.20 + 0.03 * (zz - 1.30) ** 2)
    taper = np.broadcast_to(taper, (len(s), len(z)))
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.04)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 1.0) ** 2, 0, 1) ** 0.7 * sstep(1.30, 1.42, Z3)
    crown_amt = np.interp(s, [0.0, 0.7, 0.9, 1.5, 1.8, 4.6, 4.8], [0.016, 0.018, 0.010, 0.008, 0.020, 0.020, 0.014])[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.70, 0.92, np.abs(yy))
    # pressed panel on the cargo side: the rectangle stands 4 mm proud with soft edges
    pan = sstep(2.40, 2.46, S3) * (1 - sstep(4.34, 4.40, S3)) * sstep(1.62, 1.68, Z3) * (1 - sstep(2.24, 2.30, Z3))
    D -= 0.004 * pan * side_w
    # a soft crease along the flank at the lamp line
    D -= 0.0025 * np.exp(-((Z3 - 1.20) / 0.012) ** 2) * side_w * sstep(0.3, 0.6, S3) * (1 - sstep(4.55, 4.65, S3))
    for a in (FS, RS):
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D = smax(D, -(c - 0.465) * np.ones_like(yy), 0.014)
        D -= 0.006 * np.exp(-((c - 0.49) / 0.022) ** 2) * side_w * (Z3 > 0.45)
    return D.astype(np.float32), s, y, z
