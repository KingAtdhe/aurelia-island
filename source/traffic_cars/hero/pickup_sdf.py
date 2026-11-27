"""Pickup (traffic car 07): double-cab pickup as a signed distance field, traced from Saba's reference sheet (tcars/ref/pickup.png).
Sheet coordinates: s from the front bumper (0) to the rear bumper (5.40), z up, y left. Sheet heights scaled by KZ to a 1.87 m truck."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep
from scipy import ndimage as _nd

KZ = 0.89
L, R, FS, RS = 5.40, 0.40, 0.86, 4.10
C0 = L / 2
H = 0.013
S0, S1, Y0, Z0, Z1 = -0.06, 5.46, 1.06, 0.36, 1.95
k = lambda pts: [(s, z * KZ) for s, z in pts]
NOSEB = k([(0.45, 0.47), (0.30, 0.50), (0.14, 0.57), (0.03, 0.64), (0.0, 0.70)])
TOP = k([(0.0, 0.70), (0.0, 0.92), (0.035, 0.96), (0.055, 1.00), (0.065, 1.10), (0.06, 1.22), (0.075, 1.32), (0.12, 1.38), (0.23, 1.435), (0.47, 1.494),
         (0.82, 1.543), (1.10, 1.562), (1.29, 1.575), (1.41, 1.65), (1.64, 1.807), (1.875, 1.953), (2.11, 2.041), (2.34, 2.08), (2.70, 2.095), (3.30, 2.095),
         (3.52, 2.088), (3.62, 2.04), (3.665, 1.94), (3.68, 1.80), (3.69, 1.62), (3.72, 1.600), (4.2, 1.600), (5.30, 1.600)])
TAIL = k([(5.30, 1.600), (5.335, 1.57), (5.345, 1.40), (5.345, 1.10), (5.345, 0.97), (5.39, 0.94), (5.40, 0.85), (5.40, 0.72), (5.37, 0.66), (5.30, 0.64)])
PLAN = [(0.0, 0.0), (0.004, 0.50), (0.02, 0.76), (0.07, 0.89), (0.17, 0.950), (0.35, 0.968), (0.8, 0.970), (5.2, 0.970), (5.33, 0.955), (5.385, 0.90),
        (5.40, 0.0)]
BELT = 1.36

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(5.30, 0.64 * KZ), (4.69, 0.57 * KZ), (3.55, 0.48 * KZ), (1.40, 0.46 * KZ), (0.45, 0.47 * KZ)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 2.1); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.1, 1.1)
    FS2 = (_nd.gaussian_filter(FS2[0], 4.0),) + FS2[1:]; FP = (_nd.gaussian_filter(FP[0], 4.0),) + FP[1:]
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    zz = z[None, :]; S2 = s[:, None]
    cab = sstep(1.20, 1.32, S2) * (1 - sstep(3.62, 3.70, S2))                    # greenhouse only over the cab
    taper = (cab * (0.10 * sstep(BELT - 0.01, BELT + 0.08, zz) + np.maximum(0, zz - BELT) * 0.32 + 0.6 * np.maximum(0, zz - BELT - 0.30) ** 2)
             + np.maximum(0, 0.55 - zz) * 0.25 + 0.05 * (zz - 1.05) ** 2)
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.04)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 0.97) ** 2, 0, 1) ** 0.7 * sstep(1.15, 1.26, Z3) * (1 - sstep(3.60, 3.68, S3))
    D -= crown * np.interp(s, [0.0, 1.2, 1.4, 2.0, 3.6], [0.016, 0.020, 0.010, 0.016, 0.016])[:, None, None]
    # the bed: hollow box with 45 mm walls and a floor at 0.80 m
    bed = np.maximum(np.maximum(np.abs(S3 - 4.525) - 0.755, np.abs(yy) - 0.905), 0.80 - Z3)
    D = smax(D, -bed, 0.012)
    side_w = sstep(0.62, 0.88, np.abs(yy))
    D -= 0.003 * np.exp(-((Z3 - 1.14) / 0.012) ** 2) * side_w * sstep(0.4, 0.7, S3) * (1 - sstep(5.20, 5.30, S3))
    for a in (FS, RS):                                                    # squared arches with proud black flares
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D -= 0.03 * sstep(0.62, 0.53, c) * sstep(0.46, 0.49, c) * side_w * (Z3 > 0.40)
        D = smax(D, -(c - 0.48) * np.ones_like(yy), 0.014)
    return D.astype(np.float32), s, y, z
