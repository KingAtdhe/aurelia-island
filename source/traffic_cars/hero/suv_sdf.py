"""SUV (traffic car 05): body as a signed distance field, traced from Saba's reference sheet (tcars/ref/suv.png).
Sheet coordinates: s from the nose (0) to the tail (4.70), z up, y left. Boxy body, flat roof, flared arches."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep
from scipy import ndimage as _nd

L, R, FS, RS = 4.70, 0.385, 0.80, 3.80
C0 = L / 2
H = 0.012
S0, S1, Y0, Z0, Z1 = -0.06, 4.76, 1.06, 0.26, 1.96
TOP = [(0.012, 0.62), (0.004, 0.72), (0.012, 0.86), (0.035, 0.99), (0.055, 1.10), (0.075, 1.18), (0.12, 1.236), (0.22, 1.290), (0.36, 1.330), (0.60, 1.364),
       (0.85, 1.390), (1.10, 1.410), (1.18, 1.425), (1.30, 1.52), (1.45, 1.645), (1.60, 1.765), (1.72, 1.835), (1.86, 1.866), (2.10, 1.875), (3.50, 1.876),
       (4.12, 1.872), (4.28, 1.858), (4.36, 1.820)]
TAIL = [(4.36, 1.820), (4.43, 1.660), (4.51, 1.470), (4.585, 1.300), (4.615, 1.120), (4.635, 0.940), (4.66, 0.790), (4.69, 0.690), (4.685, 0.600),
        (4.65, 0.520), (4.56, 0.460), (4.40, 0.420)]
NOSEB = [(0.36, 0.40), (0.20, 0.42), (0.08, 0.47), (0.03, 0.53), (0.012, 0.62)]
PLAN = [(0.0, 0.0), (0.005, 0.40), (0.025, 0.70), (0.07, 0.85), (0.16, 0.93), (0.32, 0.962), (0.7, 0.970), (4.0, 0.970), (4.40, 0.962), (4.56, 0.925),
        (4.65, 0.83), (4.69, 0.62), (4.70, 0.0)]
BELT = [(1.20, 1.405), (1.40, 1.400), (3.0, 1.400), (4.20, 1.402)]
BS0, BS1 = 1.20, 4.20
FEATURE = [(0.30, 1.300), (1.0, 1.305), (2.0, 1.305), (3.5, 1.305), (4.60, 1.300)]

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(4.40, 0.42), (0.36, 0.40)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 2.1); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.1, 1.1)
    FS2 = (_nd.gaussian_filter(FS2[0], 4.0),) + FS2[1:]; FP = (_nd.gaussian_filter(FP[0], 4.0),) + FP[1:]
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    belt = interp(BELT, np.clip(s, BS0, BS1)) + 1.6 * np.maximum(0, s - (BS1 + 0.02)) + 2.0 * np.maximum(0, (BS0 + 0.06) - s)
    zz = z[None, :]; bz = belt[:, None]
    taper = (0.12 * sstep(bz - 0.01, bz + 0.09, zz) + np.maximum(0, zz - bz) * 0.30 + 0.6 * np.maximum(0, zz - bz - 0.30) ** 2
             + np.maximum(0, 0.50 - zz) * 0.25 + 0.07 * (zz - 0.95) ** 2)
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.045)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 0.95) ** 2, 0, 1) ** 0.7 * sstep(1.10, 1.24, Z3)
    crown_amt = np.interp(s, [0.0, 1.0, 1.25, 1.70, 2.0, 4.2, 4.7], [0.012, 0.016, 0.010, 0.008, 0.014, 0.014, 0.010])[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.62, 0.88, np.abs(yy))
    zf = interp(FEATURE, s)[:, None, None]; along = sstep(0.20, 0.50, S3) * (1 - sstep(4.50, 4.62, S3))
    D += 0.0050 * sstep(zf + 0.002, zf - 0.028, Z3) * side_w * along
    D -= 0.0030 * np.clip(1 - np.abs(Z3 - zf - 0.004) / 0.02, 0, 1) * side_w * along
    for a in (FS, RS):                                                    # squared-off arches with proud flares
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D -= 0.024 * sstep(0.60, 0.50, c) * sstep(0.44, 0.47, c) * side_w * (Z3 > 0.30)
        D = smax(D, -(c - 0.455) * np.ones_like(yy), 0.014)
    return D.astype(np.float32), s, y, z
