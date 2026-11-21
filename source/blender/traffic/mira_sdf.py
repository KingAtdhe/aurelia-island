"""Mira body as a signed distance field (metres). Sheet coordinates: s from the nose (0) to the tail (4.25), z up, y left.
Car frame for Blender/game: x = 2.125 - s forward, origin on the ground between the axles."""
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

L, R, FS, RS = 4.25, 0.318, 0.80, 3.45            # length, wheel radius, front/rear axle s
H = 0.012                                         # voxel size
S0, S1, Y0, Z0, Z1 = -0.06, 4.31, 0.98, 0.10, 1.58

def crs(pts, n=12):
    """Catmull-Rom samples through pts."""
    P = np.array(pts, float); out = []
    for i in range(len(P) - 1):
        p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(i + 2, len(P) - 1)]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1]); return np.array(out)

TOP = [(0.0, 0.47), (0.035, 0.625), (0.12, 0.728), (0.45, 0.83), (0.98, 0.965), (1.38, 1.22), (1.80, 1.425), (2.6, 1.462), (3.40, 1.445), (3.82, 1.405), (3.95, 1.375)]
TAIL = [(3.95, 1.375), (3.99, 1.32), (4.13, 1.07), (4.20, 0.93), (4.245, 0.72), (4.25, 0.45), (4.22, 0.31), (4.12, 0.265)]
NOSEB = [(0.30, 0.26), (0.10, 0.275), (0.03, 0.34), (0.0, 0.47)]
PLAN = [(0.0, 0.0), (0.018, 0.26), (0.06, 0.46), (0.15, 0.66), (0.30, 0.805), (0.50, 0.88), (0.80, 0.90), (2.4, 0.902), (3.6, 0.897), (3.92, 0.866), (4.08, 0.80), (4.18, 0.68), (4.235, 0.46), (4.25, 0.0)]
BELT = [(0.98, 0.965), (1.07, 1.005), (2.4, 1.075), (3.52, 1.115), (3.74, 1.19), (3.95, 1.30), (4.13, 1.07)]
SHOULDER = [(0.30, 0.775), (0.62, 0.80), (1.6, 0.86), (2.8, 0.905), (3.85, 0.95), (4.18, 0.955)]

def side_poly():
    return np.vstack([crs(TOP)[:-1], crs(TAIL)[:-1], [(4.12, 0.265), (0.30, 0.26)], crs(NOSEB)])
def plan_poly():
    h = crs(PLAN); return np.vstack([h, h[::-1][1:-1] * [1, -1]])

def sdf2d(poly, a0, a1, b0, b1, res=0.002):
    """Signed distance (negative inside) of a closed polygon over a raster grid; returns (array, a0, b0, res)."""
    na, nb = int((a1 - a0) / res) + 1, int((b1 - b0) / res) + 1
    im = Image.new('L', (na, nb), 0); ImageDraw.Draw(im).polygon([((a - a0) / res, (b - b0) / res) for a, b in poly], fill=1)
    m = np.array(im, bool).T
    d = (ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)) * res
    return d, a0, b0, res
def sample2d(F, a, b):
    d, a0, b0, res = F; return ndimage.map_coordinates(d, [(a - a0) / res, (b - b0) / res], order=1, mode='nearest')

def interp(pts, x):
    P = crs(pts, 8); return np.interp(x, P[:, 0], P[:, 1])
def smax(a, b, k):
    h = np.clip(0.5 - 0.5 * (b - a) / k, 0, 1); return b + (a - b) * h + k * h * (1 - h)
def smin(a, b, k): return -smax(-a, -b, k)
def sstep(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def field():
    s = np.arange(S0, S1 + 1e-9, H); y = np.arange(-Y0, Y0 + 1e-9, H); z = np.arange(Z0, Z1 + 1e-9, H)
    FS2 = sdf2d(side_poly(), -0.2, 4.45, 0.0, 1.75); FP = sdf2d(plan_poly(), -0.2, 4.45, -1.0, 1.0)
    SS, ZZ = np.meshgrid(s, z, indexing='ij'); dside = sample2d(FS2, SS, ZZ)                       # (s, z)
    SP, YP = np.meshgrid(s, y, indexing='ij'); dplan = sample2d(FP, SP, YP)                        # (s, y)
    belt = interp(BELT, s); belt = np.where(s < 0.98, 9.0, belt)
    zz = z[None, :]
    taper = np.maximum(0, zz - belt[:, None]) * 0.62 + 0.045 * sstep(belt[:, None] - 0.03, belt[:, None] + 0.07, zz) + np.maximum(0, 0.42 - zz) * 0.30 + 0.07 * (zz - 0.80) ** 2   # tumblehome, tuck-under, curved flank
    D = smax(dside[:, None, :], dplan[:, :, None] + taper[:, None, :], 0.11)
    # crowns on bonnet, roof and tailgate: the top surfaces dome across the car
    yy = y[None, :, None]; crown = np.clip(1 - (yy / 0.88) ** 2, 0, 1) * sstep(0.62, 0.80, z[None, None, :])
    crown_amt = np.where(s < 1.0, 0.026, np.where(s < 1.75, 0.012, 0.030))[:, None, None]
    D -= crown * crown_amt
    # side sculpt: crisp shoulder line and a soft concave band along the doors
    side_w = sstep(0.55, 0.80, np.abs(yy))
    zsh = interp(SHOULDER, s)[:, None, None]; Z3 = z[None, None, :]; S3 = s[:, None, None]
    D -= 0.0065 * np.clip(1 - np.abs(Z3 - zsh) / 0.045, 0, 1) ** 1.5 * side_w * sstep(0.25, 0.6, S3) * (1 - sstep(4.10, 4.22, S3))
    zc = 0.50 + 0.045 * (S3 - 1.25) / 1.9
    D += 0.011 * np.exp(-((Z3 - zc) / 0.055) ** 2) * side_w * sstep(1.20, 1.55, S3) * (1 - sstep(2.85, 3.20, S3))
    # wheel arches with a small flared lip
    for a in (FS, RS):
        c = np.sqrt((S3 - a) ** 2 + (Z3 - R) ** 2)
        D = smax(D, -(c - 0.378) * np.ones_like(yy), 0.018)
        D -= 0.010 * np.exp(-((c - 0.405) / 0.028) ** 2) * side_w * (Z3 > 0.20)
    return D.astype(np.float32), s, y, z
