"""Porto delivery van (traffic 04): body as a signed distance field, from the approved sheet (source/art/traffic_03-05_design_sheet.jpg,
drawn by source/blender/traffic/sheet_family3.py). Sheet coordinates: s from the nose (0) to the tail (5.12), z up, y left."""
import numpy as np
from mira_sdf import crs, sdf2d, sample2d, interp, smax, smin, sstep
from scipy import ndimage as _nd

L, R, FS, RS = 5.12, 0.345, 0.82, 4.17
C0 = L / 2
H = 0.014
S0, S1, Y0, Z0, Z1 = -0.06, 5.18, 1.06, 0.24, 2.22
TOP = [(0.0, 0.56), (0.02, 0.78), (0.07, 0.95), (0.30, 1.05), (0.62, 1.12), (0.82, 1.17), (1.10, 1.58), (1.34, 1.95), (1.55, 2.10), (1.85, 2.145), (3.0, 2.15),
       (4.96, 2.15), (5.08, 2.12)]
TAIL = [(5.08, 2.12), (5.11, 2.02), (5.12, 1.50), (5.12, 0.80), (5.11, 0.52), (5.06, 0.36)]
NOSEB = [(0.25, 0.34), (0.08, 0.37), (0.02, 0.45), (0.0, 0.56)]
PLAN = [(0.0, 0.0), (0.004, 0.50), (0.02, 0.76), (0.07, 0.90), (0.16, 0.965), (0.32, 0.995), (0.7, 1.0), (4.9, 1.0), (5.02, 0.99), (5.08, 0.96),
        (5.11, 0.86), (5.12, 0.0)]
BELT = 1.30

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(5.06, 0.36), (0.25, 0.34)], crs(NOSEB)[:-1]])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, L + 0.2, 0.0, 2.4); FP = sdf2d(plan_poly(), -0.2, L + 0.2, -1.1, 1.1)
    FS2 = (_nd.gaussian_filter(FS2[0], 5.0),) + FS2[1:]; FP = (_nd.gaussian_filter(FP[0], 5.0),) + FP[1:]
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)
    zz = z[None, :]
    taper = (np.maximum(0, zz - BELT) * 0.08 + 0.9 * np.maximum(0, zz - 1.95) ** 2 + np.maximum(0, 0.60 - zz) * 0.20 + 0.03 * (zz - 1.25) ** 2)
    taper = np.broadcast_to(taper, (len(s), len(z)))
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.06)
    yy = y[None, :, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    crown = np.clip(1 - (yy / 1.0) ** 2, 0, 1) ** 0.7 * sstep(1.08, 1.17, Z3)
    crown_amt = np.interp(s, [0.0, 0.7, 0.9, 1.5, 1.8, 4.9, 5.12], [0.016, 0.018, 0.010, 0.008, 0.020, 0.020, 0.014])[:, None, None]
    D -= crown * crown_amt
    side_w = sstep(0.70, 0.92, np.abs(yy))
    box = sstep(3.26, 3.32, S3) * (1 - sstep(4.96, 5.02, S3))
    for zr in (1.72, 1.84):                                                    # two pressed ribs in the load box
        D -= 0.004 * np.exp(-((Z3 - zr) / 0.012) ** 2) * side_w * box
    # rubbing strip all along the flank (unpainted, stands 8 mm proud)
    strip = (sstep(FS + 0.42, FS + 0.46, S3) * (1 - sstep(RS - 0.46, RS - 0.42, S3)) + sstep(RS + 0.42, RS + 0.46, S3) * (1 - sstep(4.98, 5.02, S3)))
    D -= 0.008 * sstep(0.655, 0.665, Z3) * (1 - sstep(0.735, 0.745, Z3)) * side_w * strip
    for a in (FS, RS):
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D = smax(D, -(c - 0.42) * np.ones_like(yy), 0.014)
        D -= 0.006 * np.exp(-((c - 0.445) / 0.022) ** 2) * side_w * (Z3 > 0.40)
    return D.astype(np.float32), s, y, z
