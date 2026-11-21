"""Vela body as a signed distance field (metres). Sheet coordinates: s from the nose (0) to the tail (4.70), z up, y left.
Car frame for Blender/game: x = 2.35 - s forward, origin on the ground at the body's mid length. Drawn from the approved sheet (sheet_saloon.py)."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep

L, R, FS, RS = 4.70, 0.335, 0.93, 3.73
C0 = L / 2
H = 0.012
S0, S1, Y0, Z0, Z1 = -0.06, 4.76, 1.0, 0.10, 1.56

TOP = [(0.0, 0.50), (0.035, 0.645), (0.12, 0.735), (0.50, 0.805), (1.00, 0.885), (1.36, 0.945), (1.70, 1.17), (2.00, 1.365), (2.55, 1.448), (3.05, 1.435),
       (3.40, 1.33), (3.78, 1.082), (4.20, 1.05), (4.58, 1.032), (4.665, 1.02)]
TAIL = [(4.665, 1.02), (4.69, 0.96), (4.70, 0.80), (4.695, 0.55), (4.67, 0.37), (4.58, 0.275)]
NOSEB = [(0.36, 0.255), (0.12, 0.27), (0.03, 0.35), (0.0, 0.50)]
PLAN = [(0.0, 0.0), (0.02, 0.28), (0.07, 0.50), (0.17, 0.70), (0.34, 0.85), (0.58, 0.905), (0.95, 0.92), (2.6, 0.92), (3.9, 0.915), (4.30, 0.89), (4.50, 0.84),
        (4.62, 0.74), (4.68, 0.55), (4.70, 0.0)]
BELT = [(1.36, 0.945), (1.42, 0.985), (2.4, 1.04), (3.30, 1.075), (3.62, 1.10), (3.80, 1.085)]
FEATURE = [(0.40, 0.795), (1.0, 0.818), (1.6, 0.835), (2.8, 0.865), (3.9, 0.895), (4.68, 0.905)]

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(4.58, 0.275), (0.36, 0.255)], crs(NOSEB)])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, 4.9, 0.0, 1.75); FP = sdf2d(plan_poly(), -0.2, 4.9, -1.05, 1.05)
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    belt = interp(BELT, np.clip(s, 1.36, 3.80)) + 1.6 * np.maximum(0, s - 3.66) + 1.6 * np.maximum(0, 1.46 - s)      # taper fades smoothly into bonnet and boot deck
    zz = z[None, :]
    taper = (np.maximum(0, zz - belt[:, None]) * 0.66 + 0.045 * sstep(belt[:, None] - 0.03, belt[:, None] + 0.07, zz)
             + np.maximum(0, 0.40 - zz) * 0.30 + 0.05 * (zz - 0.82) ** 2)                 # tumblehome, tuck-under, gently curved flank
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.10)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 0.90) ** 2, 0, 1) * sstep(0.66, 0.82, Z3)
    crown_amt = np.where(s < 1.36, 0.024, np.where(s < 2.0, 0.010, np.where(s < 3.80, 0.028, 0.018)))[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.58, 0.82, np.abs(yy))
    # one crisp feature line: the panel above stands proud, the face below steps back by 5 mm
    zf = interp(FEATURE, s)[:, None, None]; along = sstep(0.35, 0.65, S3) * (1 - sstep(4.55, 4.68, S3))
    D += 0.0050 * sstep(zf + 0.002, zf - 0.028, Z3) * side_w * along
    D -= 0.0030 * np.clip(1 - np.abs(Z3 - zf - 0.004) / 0.02, 0, 1) * side_w * along
    # low rising groove above the sill
    zc = 0.43 + 0.045 * (S3 - 1.45) / 1.85
    D += 0.006 * np.exp(-((Z3 - zc) / 0.035) ** 2) * side_w * sstep(1.40, 1.60, S3) * (1 - sstep(3.15, 3.35, S3))
    # wheel arches with a small lip
    for a in (FS, RS):
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D = smax(D, -(c - 0.395) * np.ones_like(yy), 0.016)
        D -= 0.008 * np.exp(-((c - 0.42) / 0.026) ** 2) * side_w * (Z3 > 0.20)
    return D.astype(np.float32), s, y, z
