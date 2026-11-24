# join the bake tiles of bake_island.py into bake_island.png: R = sun visibility, G = sky light (occlusion), 4096 wide
import bpy, numpy as np, os, sys
from PIL import Image
D = os.environ.get('OUT', '/home/claude/bake_isl/'); TX, TZ = 4, 3; WOUT = int(os.environ.get('WOUT', '4096'))
def load(n):
    im = bpy.data.images.load(D + n); w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, 0]; bpy.data.images.remove(im); return a
rows = []
for j in range(TZ):
    row = []
    for i in range(TX):
        sun, free, sky = load('sun_%d_%d.exr' % (i, j)), load('sunfree_%d_%d.exr' % (i, j)), load('sky_%d_%d.exr' % (i, j))
        vis = np.clip(sun / np.maximum(free, 1e-4), 0, 1); vis[free < 1e-3] = 1.0
        row.append((vis, sky))
    rows.append(row)
sky_all = np.concatenate([np.concatenate([t[1] for t in r], 1) for r in rows], 0)
ref = np.percentile(sky_all[sky_all > 0.05], 95)
vis = np.concatenate([np.concatenate([t[0] for t in r], 1) for r in rows], 0); ao = np.clip(sky_all / ref, 0, 1)
# image row 0 = the smallest game z (the camera looked down with Blender +y = -z at the top of the picture)
# the road inside tunnels is under the hill: no sun, little sky (the bake saw the tube from above)
import json
W = json.load(open('/home/claude/aurelia-island/godot/assets/world.json')); H_, W_ = vis.shape
for ri, a, n in W['tunnels']:
    r = W['roads'][ri]; p = np.array(r['pts']).reshape(-1, 3)[a:a + n + 1]; hw = r['w'] / 2 + 1.5
    yy, xx = np.mgrid[0:H_, 0:W_]
    x0, x1 = p[:, 0].min() - 20, p[:, 0].max() + 20; z0, z1 = p[:, 2].min() - 20, p[:, 2].max() + 20
    c0, c1 = int((x0 + 2400) / 4800 * W_), int((x1 + 2400) / 4800 * W_) + 1; r0, r1 = int((z0 + 1680) / 3360 * H_), int((z1 + 1680) / 3360 * H_) + 1
    X = (xx[r0:r1, c0:c1] + 0.5) / W_ * 4800 - 2400; Z = (yy[r0:r1, c0:c1] + 0.5) / H_ * 3360 - 1680
    best = np.full(X.shape, 1e9); depth = np.zeros(X.shape)
    for k in range(len(p)):
        d = np.hypot(X - p[k, 0], Z - p[k, 2]); m = d < best; best[m] = d[m]; depth[m] = min(k, len(p) - 1 - k) * 5.0
    inside = (best < hw) * np.clip(depth / 12.0, 0, 1)
    vis[r0:r1, c0:c1] *= 1 - inside; ao[r0:r1, c0:c1] = ao[r0:r1, c0:c1] * (1 - inside) + 0.15 * inside

out = np.stack([vis, ao, np.zeros_like(vis)], -1)
im = Image.fromarray((out * 255 + 0.5).astype(np.uint8)); H = int(round(WOUT * out.shape[0] / out.shape[1]))
im.resize((WOUT, H), Image.LANCZOS).save(D + 'bake_island.png')
Image.fromarray(((vis * 0.6 + ao * 0.4) * 255).astype(np.uint8)).resize((1600, int(1600 * out.shape[0] / out.shape[1]))).save(D + 'preview.png')
print('vis', vis.mean(), 'ao', ao.mean(), out.shape, '->', WOUT, H)
# small sun-visibility map the game reads on the CPU to dim the cars' sunlight in shade (assets/island/bake_sun.bin)
import struct
sm = np.array(Image.fromarray((vis * 255 + 0.5).astype(np.uint8)).resize((2048, 1434), Image.BILINEAR), np.uint8)
with open(D + 'bake_sun.bin', 'wb') as f: f.write(struct.pack('<II', 2048, 1434)); f.write(sm.tobytes())
