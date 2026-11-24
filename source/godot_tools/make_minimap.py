"""Minimap picture of the island for the game HUD (godot/assets/minimap.png): land shaded from the height map, sea, lakes,
and every road by type (highway, road, street, dirt trail, circuit). 2 m per pixel over the island bounds, x right, z down."""
import json, base64, numpy as np
from PIL import Image, ImageDraw, ImageFilter
R = '/home/claude/aurelia-island/'
W = json.load(open(R + 'godot/assets/world.json')); hm = W['heightmap']
H = np.frombuffer(base64.b64decode(json.load(open(R + 'data/height.json'))['b64']), '<i2').astype(np.float32).reshape(hm['ny'], hm['nx']) * hm['scale']
X0, Z0, SX, SZ, MPP, SS = -2400.0, -1680.0, 4800.0, 3360.0, 2.0, 2          # bounds, metres per pixel, supersampling
w, h = int(SX / MPP), int(SZ / MPP)
# height map rows run along -z (y0 is -z): flip so row 0 is z = -1680
Hg = H[::-1, :]
hi = np.array(Image.fromarray(Hg).resize((w, h), Image.BILINEAR))
land = hi > 0.2
# hill shading from the slope, light from the north-west
gy, gx = np.gradient(hi, MPP)
shade = np.clip(0.75 + (-gx * 0.6 - gy * 0.6) * 0.9, 0.45, 1.15)
base = np.zeros((h, w, 3), np.float32)
lowc, highc = np.array([0.16, 0.22, 0.19]), np.array([0.30, 0.30, 0.28])
t = np.clip(hi / 110.0, 0, 1)[..., None]
base[:] = (lowc * (1 - t) + highc * t) * shade[..., None]
sea = np.array([0.06, 0.13, 0.19]); shallow = np.array([0.08, 0.19, 0.25])
depth = np.clip(-hi / 6.0, 0, 1)[..., None]
base[~land] = (shallow * (1 - depth) + sea * depth)[~land]
img = Image.fromarray((base.clip(0, 1) * 255).astype(np.uint8)).resize((w * SS, h * SS), Image.BILINEAR)
d = ImageDraw.Draw(img)
P = lambda x, z: ((x - X0) / MPP * SS, (z - Z0) / MPP * SS)
for x, y, z, r in W['lakes']:
    cx, cy = P(x, z); rr = r / MPP * SS; d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(18, 44, 60))
STY = {'hwy': ((236, 196, 112), 16.0), 'road': ((222, 224, 226), 11.0), 'rbt': ((222, 224, 226), 10.0), 'street': ((170, 176, 182), 9.0),
       'dirt': ((160, 128, 92), 6.0), 'circuit': ((235, 90, 70), 14.0)}
order = ['dirt', 'street', 'road', 'rbt', 'hwy', 'circuit']
for typ in order:
    col, wid = STY[typ]
    for r in W['roads']:
        if r['type'] != typ: continue
        p = np.array(r['pts']).reshape(-1, 3); pts = [P(a[0], a[2]) for a in p]
        if r['closed']: pts.append(pts[0])
        lw = max(2, int(wid / MPP * SS * 0.9))
        d.line(pts, fill=(20, 22, 24), width=lw + 4 * SS // 2, joint='curve')          # dark casing
    for r in W['roads']:
        if r['type'] != typ: continue
        p = np.array(r['pts']).reshape(-1, 3); pts = [P(a[0], a[2]) for a in p]
        if r['closed']: pts.append(pts[0])
        d.line(pts, fill=col, width=max(2, int(wid / MPP * SS * 0.9)), joint='curve')
img = img.resize((w, h), Image.LANCZOS)
img.save(R + 'godot/assets/minimap.png'); print(img.size)
