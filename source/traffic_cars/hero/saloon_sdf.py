"""Saloon (traffic car 04): body as a signed distance field, traced from Saba's reference sheet (tcars/ref/saloon.png).
Sheet coordinates: s from the nose (0) to the tail (4.77), z up, y left. Side view scaled 4.80 m / 888 px."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep
from scipy import ndimage as _nd

L, R, FS, RS = 4.77, 0.345, 0.80, 3.86
C0 = L / 2
H = 0.012
S0, S1, Y0, Z0, Z1 = -0.06, 4.83, 1.0, 0.10, 1.56
TOP = [(0.004, 0.50), (0.012, 0.63), (0.035, 0.715), (0.075, 0.765), (0.15, 0.818), (0.25, 0.862), (0.40, 0.905), (0.56, 0.940), (0.72, 0.966), (0.90, 0.988),
       (1.10, 1.004), (1.28, 1.016), (1.36, 1.030), (1.50, 1.105), (1.67, 1.190), (1.83, 1.265), (1.99, 1.330), (2.15, 1.383), (2.32, 1.415), (2.50, 1.432),
       (2.70, 1.442), (2.90, 1.440), (3.10, 1.428), (3.29, 1.405), (3.45, 1.373), (3.61, 1.325), (3.77, 1.270), (3.94, 1.205), (4.10, 1.135), (4.24, 1.070),
       (4.36, 1.035), (4.50, 1.010), (4.62, 0.993), (4.70, 0.980)]
TAIL = [(4.70, 0.980), (4.738, 0.955), (4.758, 0.880), (4.768, 0.740), (4.770, 0.580), (4.764, 0.440), (4.745, 0.340), (4.70, 0.275), (4.62, 0.245)]
NOSEB = [(0.42, 0.205), (0.17, 0.212), (0.05, 0.240), (0.008, 0.300), (0.0, 0.40), (0.004, 0.50)]
PLAN = [(0.0, 0.0), (0.02, 0.30), (0.07, 0.52), (0.17, 0.71), (0.34, 0.855), (0.58, 0.915), (0.95, 0.932), (2.6, 0.935), (3.9, 0.93), (4.30, 0.905),
        (4.52, 0.85), (4.66, 0.74), (4.735, 0.55), (4.77, 0.0)]
BELT = [(1.36, 0.995), (1.45, 1.000), (2.4, 1.030), (3.30, 1.058), (3.70, 1.078), (3.88, 1.080)]
BS0, BS1 = 1.36, 3.88
FEATURE = [(0.40, 0.800), (1.0, 0.818), (1.6, 0.832), (2.8, 0.858), (3.9, 0.888), (4.74, 0.905)]

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(4.62, 0.245), (0.42, 0.205)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 1.75); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.05, 1.05)
    FS2 = (_nd.gaussian_filter(FS2[0], 4.0),) + FS2[1:]; FP = (_nd.gaussian_filter(FP[0], 4.0),) + FP[1:]
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    belt = interp(BELT, np.clip(s, BS0, BS1)) + 1.6 * np.maximum(0, s - (BS1 - 0.14)) + 1.6 * np.maximum(0, (BS0 + 0.10) - s)
    zz = z[None, :]; bz = belt[:, None]
    taper = (np.maximum(0, zz - bz) * 0.70 + 0.8 * np.maximum(0, zz - bz - 0.25) ** 2 + 0.045 * sstep(bz - 0.03, bz + 0.07, zz)
             + np.maximum(0, 0.38 - zz) * 0.30 + 0.05 * (zz - 0.80) ** 2)
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.06)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 0.90) ** 2, 0, 1) ** 0.7 * sstep(0.66, 0.82, Z3)
    crown_amt = np.interp(s, [0.0, 1.20, 1.45, 1.80, 2.20, 3.70, 4.10, 4.8], [0.020, 0.024, 0.014, 0.010, 0.024, 0.026, 0.018, 0.014])[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.58, 0.82, np.abs(yy))
    zf = interp(FEATURE, s)[:, None, None]; along = sstep(0.35, 0.65, S3) * (1 - sstep(4.60, 4.72, S3))
    D += 0.0050 * sstep(zf + 0.002, zf - 0.028, Z3) * side_w * along
    D -= 0.0030 * np.clip(1 - np.abs(Z3 - zf - 0.004) / 0.02, 0, 1) * side_w * along
    zc = 0.40 + 0.04 * (S3 - 1.45) / 2.0
    D += 0.006 * np.exp(-((Z3 - zc) / 0.035) ** 2) * side_w * sstep(1.40, 1.60, S3) * (1 - sstep(3.30, 3.50, S3))
    for a in (FS, RS):
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D = smax(D, -(c - 0.405) * np.ones_like(yy), 0.016)
        D -= 0.008 * np.exp(-((c - 0.43) / 0.026) ** 2) * side_w * (Z3 > 0.20)
    return D.astype(np.float32), s, y, z
