"""Tera compact crossover (traffic 03): body as a signed distance field, from the approved sheet (source/art/traffic_03-05_design_sheet.jpg,
drawn by source/blender/traffic/sheet_family3.py). Sheet coordinates: s from the nose (0) to the tail (4.48), z up, y left."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep

L, R, FS, RS = 4.48, 0.355, 0.86, 3.56
C0 = L / 2
H = 0.012
S0, S1, Y0, Z0, Z1 = -0.06, 4.54, 1.02, 0.20, 1.74
TOP = [(0.0, 0.58), (0.025, 0.78), (0.10, 0.90), (0.50, 0.985), (1.00, 1.075), (1.27, 1.115), (1.62, 1.40), (1.95, 1.60), (2.40, 1.655), (3.40, 1.655),
       (4.05, 1.63), (4.32, 1.585)]
TAIL = [(4.32, 1.585), (4.40, 1.45), (4.45, 1.22), (4.47, 1.00), (4.48, 0.75), (4.465, 0.50), (4.40, 0.34)]
NOSEB = [(0.30, 0.31), (0.10, 0.33), (0.03, 0.42), (0.0, 0.58)]
PLAN = [(0.0, 0.0), (0.012, 0.36), (0.05, 0.62), (0.14, 0.80), (0.30, 0.90), (0.56, 0.928), (1.0, 0.93), (3.9, 0.93), (4.28, 0.918), (4.41, 0.87),
        (4.465, 0.72), (4.48, 0.0)]
BELT = [(1.27, 1.115), (1.34, 1.16), (2.4, 1.19), (3.5, 1.22), (4.22, 1.25)]
BS0, BS1 = 1.27, 4.22
FEATURE = [(0.40, 0.99), (1.6, 1.05), (2.8, 1.085), (3.9, 1.12), (4.44, 1.135)]

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(4.40, 0.34), (0.30, 0.31)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 1.95); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.05, 1.05)
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    belt = interp(BELT, np.clip(s, BS0, BS1)) + 1.6 * np.maximum(0, s - (BS1 + 0.02)) + 1.8 * np.maximum(0, (BS0 + 0.08) - s)
    zz = z[None, :]; bz = belt[:, None]
    taper = (0.06 * sstep(bz - 0.01, bz + 0.08, zz) + np.maximum(0, zz - bz) * 0.36 + 0.3 * np.maximum(0, zz - bz - 0.30) ** 2
             + np.maximum(0, 0.46 - zz) * 0.25 + 0.06 * (zz - 0.85) ** 2)
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.08)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 0.92) ** 2, 0, 1) ** 0.8 * sstep(0.88, 1.02, Z3)
    crown_amt = np.interp(s, [0.0, 1.0, 1.27, 1.70, 2.0, 4.1, 4.48], [0.014, 0.018, 0.010, 0.008, 0.016, 0.016, 0.010])[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.60, 0.86, np.abs(yy))
    # shoulder line: the panel above stands proud, a sharp step below
    zf = interp(FEATURE, s)[:, None, None]; along = sstep(0.45, 0.70, S3) * (1 - sstep(4.38, 4.46, S3))
    D += 0.0050 * sstep(zf + 0.002, zf - 0.028, Z3) * side_w * along
    D -= 0.0030 * np.clip(1 - np.abs(Z3 - zf - 0.004) / 0.02, 0, 1) * side_w * along
    # lower door sculpt rising rearwards
    zc = 0.62 + 0.08 * (S3 - 1.40) / 1.90
    D += 0.005 * np.exp(-((Z3 - zc) / 0.04) ** 2) * side_w * sstep(1.38, 1.55, S3) * (1 - sstep(3.15, 3.32, S3))
    for a in (FS, RS):                                                    # arches with proud flares (the black cladding)
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D -= 0.020 * sstep(0.535, 0.49, c) * sstep(0.43, 0.455, c) * side_w * (Z3 > 0.30)
        D = smax(D, -(c - 0.43) * np.ones_like(yy), 0.012)
    # sills step out a little under the doors (cladding)
    D -= 0.010 * sstep(0.47, 0.43, Z3) * side_w * sstep(FS + 0.40, FS + 0.50, S3) * (1 - sstep(RS - 0.50, RS - 0.40, S3))
    return D.astype(np.float32), s, y, z
