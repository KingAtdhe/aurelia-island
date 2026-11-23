"""Background traffic car from a 4-view reference sheet (side, front, rear, 3/4) on a plain background.
Body = intersection of the side outline with the front/rear width profile (rounded in plan), marched into a mesh;
wheels detected in the side view and modelled as separate wheels; the sheet is projected on as the paint.
usage: python3 build_tcar.py -- <name>"""
import sys, os, json, math
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

REF = '/home/claude/tcars/ref/'; OUT = '/home/claude/tcars/out/'; os.makedirs(OUT, exist_ok=True)
# name: file, real length (m), manual view boxes (x, y, w, h) if the automatic split fails
CARS = {
    'hatch':  dict(file='hatch.png', L=4.15),
    'saloon': dict(file='saloon.png', L=4.95),
    'suv':    dict(file='suv.png', L=4.70),
    'van':    dict(file='van.jpg', L=4.80, thr=7, close=8, hull=True, wheels=[(0.84, 0.42), (3.80, 0.42)], boxes=dict(side=(55, 225, 770, 450), front=(930, 225, 495, 445), rear=(170, 875, 425, 475))),
    'pickup': dict(file='pickup.png', L=5.35),
}
name = sys.argv[sys.argv.index('--') + 1]
C = CARS[name]
img = np.asarray(Image.open(REF + C['file']).convert('RGB')).astype(np.float32)
H0, W0 = img.shape[:2]
bg = np.median(np.concatenate([img[:6].reshape(-1, 3), img[-6:].reshape(-1, 3), img[:, :6].reshape(-1, 3)]), 0)
lum = img.mean(-1)


def mask_of(a):
    m = np.abs(a - bg).max(-1) > C.get('thr', 14)
    m = ndimage.binary_opening(m, iterations=2); m = ndimage.binary_closing(m, iterations=C.get('close', 1)); m = ndimage.binary_fill_holes(m)
    lab, n = ndimage.label(m)
    if n == 0: return m
    sizes = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (np.argmax(sizes) + 1)
    return ndimage.binary_fill_holes(m)


if 'boxes' in C:
    boxes = C['boxes']
else:
    m = mask_of(img); lab, n = ndimage.label(np.abs(img - bg).max(-1) > 14)
    objs = [(s, (lab[s] == i + 1).sum()) for i, s in enumerate(ndimage.find_objects(lab))]
    objs = [(s[1].start, s[0].start, s[1].stop - s[1].start, s[0].stop - s[0].start) for s, a in objs if a > 5000]
    top = sorted([o for o in objs if o[1] < H0 * 0.45], key=lambda o: -o[2])
    bot = sorted([o for o in objs if o[1] >= H0 * 0.45], key=lambda o: o[0])
    boxes = dict(side=top[0], front=top[1], rear=bot[0])


def crop(b, pad=6):
    x, y, w, h = b
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W0, x + w + pad), min(H0, y + h + pad)
    a = img[y0:y1, x0:x1]; m = mask_of(a)
    # cut the ground shadow: nothing below the lowest tyre pixel
    dark = (a.mean(-1) < 75) & m
    rows = np.where(dark.any(1))[0]
    if len(rows): m[rows.max() + 1:] = False
    ys, xs = np.where(m); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if C.get('hull'):            # light paint on a light background: the outline is completed by its convex hull above the sills
        from skimage.morphology import convex_hull_image
        hm = convex_hull_image(m); hm[int(m.shape[0] * 0.78):] = False; m = m | hm
    return a, m


side, ms = crop(boxes['side']); front, mf = crop(boxes['front']); rear, mr = crop(boxes['rear'])
L = C['L']; s = L / ms.shape[1]; Hc = ms.shape[0] * s                       # metres per side-view pixel, car height
print(name, 'side px', ms.shape, 'height %.2f m' % Hc)


def half_width(m):          # half width per row (top..bottom), mirrors clipped to the body width
    sf = Hc / m.shape[0]; w = np.array([(np.ptp(r.nonzero()[0]) + 1) if r.any() else 0 for r in m], float) * sf / 2
    body = np.median(w[int(len(w) * 0.55):int(len(w) * 0.85)])
    return np.minimum(w, body * 1.01), sf


hwf, sff = half_width(mf); hwr, sfr = half_width(mr)
Wc = 2 * max(hwf.max(), hwr.max())
k = min(1.0, 0.44 * L / Wc); hwf *= k; hwr *= k; Wc *= k                 # generated front views often run wide: keep real-car proportions
print('width %.2f m' % Wc)

# wheels: tyre contact patches are the dark runs along the bottom rows; each wheel is the dark blob grown from its patch
dark = (side.mean(-1) < 80) & ms
hpx = ms.shape[0]; band = dark[int(hpx * 0.96):].any(0)
runs = []; x = 0
while x < len(band):
    if band[x]:
        x0 = x
        while x < len(band) and band[x]: x += 1
        runs.append((x0, x))
    else: x += 1
runs = sorted(runs, key=lambda r: r[1] - r[0])[-2:]
wheels = []
for x0, x1 in runs:
    cx = (x0 + x1) / 2
    lab, n = ndimage.label(dark & (np.arange(hpx)[:, None] > hpx * 0.4))
    k = lab[hpx - 2, int(cx)] if dark[hpx - 2, int(cx)] else lab[hpx - 4, int(cx)]
    ys, xs = np.where(lab == k) if k else (np.array([hpx - 1]), np.array([x0, x1]))
    r = min((ys.max() - ys.min()) / 2, (xs.max() - xs.min()) / 2, 0.12 * ms.shape[1])
    wheels.append((cx * s, r * s, r * s))                                   # x from the nose, hub height = radius, radius (m)
if 'wheels' in C: wheels = [(wx, wr, wr) for wx, wr in C['wheels']]
R = float(np.mean([w[2] for w in wheels]))
wheels.sort(); print('wheels', [tuple(round(float(v), 2) for v in w) for w in wheels])

# volume
vox = 0.03
nx, ny, nz = int(L / vox) + 12, int(Wc / vox) + 12, int(Hc / vox) + 12
X = (np.arange(nx) - 6) * vox; Y = (np.arange(ny) - 6) * vox - Wc / 2; Z = (np.arange(nz) - 6) * vox
xi = np.clip((X / s).astype(int), 0, ms.shape[1] - 1); zi = np.clip(((Hc - Z) / s).astype(int), 0, ms.shape[0] - 1)
inside_side = ms[zi[None, :], xi[:, None]] & (X[:, None] >= 0) & (X[:, None] <= L) & (Z[None, :] >= 0) & (Z[None, :] <= Hc)     # (nx, nz)
zf = np.clip(((Hc - Z) / sff).astype(int), 0, len(hwf) - 1); zr = np.clip(((Hc - Z) / sfr).astype(int), 0, len(hwr) - 1)
t = np.clip((X / L - 0.3) / 0.4, 0, 1); t = t * t * (3 - 2 * t)
hw = hwf[zf][None, :] * (1 - t[:, None]) + hwr[zr][None, :] * t[:, None]      # (nx, nz)
px = np.abs(X - L / 2) / (L / 2)                                                     # rounded corners in plan
plan = np.clip(1 - px ** 10, 0, 1) ** (1 / 5)
hw = hw * (0.55 + 0.45 * plan[:, None])
vol = inside_side[:, None, :] & (np.abs(Y)[None, :, None] <= hw[:, None, :])
# wheel arches cut into the body sides, wheels modelled separately
for wx, wz, wr in wheels:
    d = np.hypot(X[:, None] - wx, Z[None, :] - wz)
    arch = d < wr * 1.12
    vol &= ~(arch[:, None, :] & (np.abs(Y)[None, :, None] > Wc / 2 - 0.34))
vol &= (Z >= R * 0.5)[None, None, :]                  # ground clearance: the wheels are separate, nothing hangs down to the road
for wx, wz, wr in wheels:                             # full wheel wells, so no tyre-coloured body shows beside the wheels
    d = np.hypot(X[:, None] - wx, Z[None, :] - wz)
    vol &= ~((d < wr * 1.08)[:, None, :] & (np.abs(Y)[None, :, None] > Wc / 2 - 0.55))
vol = ndimage.binary_opening(vol, iterations=1)
vol[:3] = vol[-3:] = False; vol[:, :3] = vol[:, -3:] = False; vol[:, :, :3] = vol[:, :, -3:] = False      # closed at every side
f = ndimage.gaussian_filter(vol.astype(np.float32), 1.6)
verts, faces, normals, _ = measure.marching_cubes(f, 0.5, spacing=(vox, vox, vox))
verts += np.array([X[0], Y[0], Z[0]])
np.savez(OUT + name + '_mc.npz', v=verts, f=faces)

# texture atlas: side on top, front and rear underneath, one tyre
AW = 2048; sh = int(AW * side.shape[0] / side.shape[1])
fw = int(AW * 0.3); fh = int(fw * front.shape[0] / front.shape[1]); rw = int(AW * 0.3); rh = int(rw * rear.shape[0] / rear.shape[1])
AH = 1 << int(math.ceil(math.log2(sh + max(fh, rh) + 8)))
atlas = np.full((AH, AW, 3), np.array(bg) * 0 + 128, np.float32)
def fill(dst_y, dst_x, a, m, w, h):
    im = Image.fromarray(a.astype(np.uint8)).resize((w, h), Image.LANCZOS); mm = Image.fromarray((m * 255).astype(np.uint8)).resize((w, h))
    a2 = np.asarray(im).astype(np.float32); m2 = ndimage.binary_erosion(np.asarray(mm) > 127, iterations=3)
    # outside the outline: nearest body colour, so edge texels never show the grey background
    idx = ndimage.distance_transform_edt(~m2, return_distances=False, return_indices=True)
    a2 = a2[idx[0], idx[1]]
    atlas[dst_y:dst_y + h, dst_x:dst_x + w] = a2
fill(0, 0, side, ms, AW, sh); fill(sh + 4, 0, front, mf, fw, fh); fill(sh + 4, fw + 8, rear, mr, rw, rh)
Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(OUT + name + '_atlas.png')
json.dump(dict(L=L, H=Hc, W=Wc, wheels=wheels, R=R, AW=AW, AH=AH, side=[0, 0, AW, sh], front=[0, sh + 4, fw, fh], rear=[fw + 8, sh + 4, rw, rh],
               hwf=hwf.tolist(), hwr=hwr.tolist(), top=[(int(np.argmax(c)) if c.any() else 0) / ms.shape[0] for c in ms.T]), open(OUT + name + '.json', 'w'))
print('mesh', len(verts), 'verts', len(faces), 'faces; atlas', AW, AH)
