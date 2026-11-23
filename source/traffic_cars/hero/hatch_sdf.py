"""Hatch (traffic car 03): body as a signed distance field, traced from Saba's reference sheet (tcars/ref/hatch.png).
Sheet coordinates: s from the nose (0) to the tail (4.15), z up, y left. Heights from the image scaled by KZ to a 1.53 m car."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep

KZ = 0.92
L, R, FS, RS = 4.15, 0.335, 0.725, 3.55
C0 = L / 2
H = 0.012
S0, S1, Y0, Z0, Z1 = -0.06, 4.21, 1.0, 0.10, 1.68
k = lambda pts: [(s, z * KZ) for s, z in pts]
TOP = k([(0.008, 0.672), (0.041, 0.751), (0.081, 0.887), (0.122, 0.927), (0.195, 0.98), (0.29, 1.02), (0.49, 1.078), (0.68, 1.114), (0.88, 1.14),
         (0.97, 1.157), (1.07, 1.203), (1.265, 1.323), (1.46, 1.433), (1.654, 1.528), (1.849, 1.595), (2.04, 1.632), (2.34, 1.652), (2.63, 1.658),
         (2.92, 1.652), (3.21, 1.632), (3.50, 1.595), (3.66, 1.565)])
TAIL = k([(3.66, 1.565), (3.72, 1.55), (3.78, 1.44), (3.89, 1.27), (3.99, 1.142), (4.05, 1.07), (4.095, 0.96), (4.13, 0.80), (4.148, 0.66),
          (4.15, 0.52), (4.142, 0.375), (4.11, 0.333), (4.07, 0.30), (3.99, 0.27)])
NOSEB = k([(0.40, 0.215), (0.20, 0.223), (0.097, 0.24), (0.041, 0.27), (0.008, 0.32), (0.0, 0.45), (0.0, 0.58), (0.008, 0.672)])
PLAN = [(0.0, 0.0), (0.02, 0.30), (0.06, 0.52), (0.15, 0.71), (0.30, 0.83), (0.52, 0.875), (0.9, 0.885), (2.6, 0.885), (3.45, 0.88), (3.75, 0.86),
        (3.95, 0.80), (4.07, 0.68), (4.13, 0.48), (4.15, 0.0)]
BELT = [(1.12, 1.022), (1.30, 1.03), (2.4, 1.045), (3.30, 1.06), (3.50, 1.09)]
BS0, BS1 = 1.12, 3.50
FEATURE = [(0.30, 0.875), (1.0, 0.885), (1.8, 0.895), (2.8, 0.910), (3.6, 0.925), (4.08, 0.935)]

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(3.99, 0.27 * KZ), (3.90, 0.215), (0.40, 0.215 * KZ)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 1.70); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.05, 1.05)
    from scipy import ndimage as _nd; FS2 = (_nd.gaussian_filter(FS2[0], 3.0),) + FS2[1:]; FP = (_nd.gaussian_filter(FP[0], 3.0),) + FP[1:]   # de-stair the raster distance
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    belt = interp(BELT, np.clip(s, BS0, BS1)) + 1.6 * np.maximum(0, s - (BS1 - 0.10)) + 1.6 * np.maximum(0, (BS0 + 0.10) - s)
    zz = z[None, :]
    taper = (np.maximum(0, zz - belt[:, None]) * 0.40 + 0.9 * np.maximum(0, zz - belt[:, None] - 0.30) ** 2 + 0.04 * sstep(belt[:, None] - 0.03, belt[:, None] + 0.07, zz)
             + np.maximum(0, 0.36 - zz) * 0.30 + 0.05 * (zz - 0.75) ** 2)
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.10)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 0.86) ** 2, 0, 1) ** 0.5 * sstep(0.62, 0.78, Z3)
    crown_amt = np.interp(s, [0.0, 0.95, 1.20, 1.55, 1.85, 3.50, 3.80, 4.2], [0.020, 0.024, 0.016, 0.010, 0.022, 0.026, 0.016, 0.012])[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.56, 0.80, np.abs(yy))
    zf = interp(FEATURE, s)[:, None, None]; along = sstep(0.25, 0.55, S3) * (1 - sstep(4.00, 4.12, S3))
    D += 0.0045 * sstep(zf + 0.002, zf - 0.028, Z3) * side_w * along
    D -= 0.0028 * np.clip(1 - np.abs(Z3 - zf - 0.004) / 0.02, 0, 1) * side_w * along
    zc = 0.36 + 0.03 * (S3 - 1.15) / 2.0                            # low groove above the sill
    D += 0.005 * np.exp(-((Z3 - zc) / 0.03) ** 2) * side_w * sstep(1.10, 1.30, S3) * (1 - sstep(2.95, 3.15, S3))
    for a in (FS, RS):
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D = smax(D, -(c - 0.395) * np.ones_like(yy), 0.016)
        D -= 0.008 * np.exp(-((c - 0.42) / 0.026) ** 2) * side_w * (Z3 > 0.20)
    return D.astype(np.float32), s, y, z
