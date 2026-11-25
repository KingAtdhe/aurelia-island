# overcast skies for rain (day and night), 2048 x 1024 equirect like the other skies: a low grey deck built from the web
# game's cloud texture at two scales, darker underneath, lighter towards the horizon haze. usage: python3 sky_rain.py <out>
import sys, math, numpy as np
from PIL import Image
OUT = sys.argv[1]; W, H = 2048, 1024
cl = np.asarray(Image.open('/home/claude/aurelia-island/data/clouds.png').convert('RGBA')).astype(np.float32) / 255
ys, xs = np.mgrid[0:H, 0:W]
lon = (xs + 0.5) / W * 2 * math.pi - math.pi; lat = math.pi / 2 - (ys + 0.5) / H * math.pi
dx = np.cos(lat) * np.sin(lon); dy = np.cos(lat) * np.cos(lon); dz = np.sin(lat)
up = dz > 0.01
def tex(s, o):
    u = np.where(up, dx / np.maximum(dz, 0.01), 0) / s + o; v = np.where(up, dy / np.maximum(dz, 0.01), 0) / s + o * 0.7
    cs = cl.shape[0]; iu = ((u % 1) * cs).astype(int) % cs; iv = ((v % 1) * cs).astype(int) % cs
    return cl[iv, iu, 3]
from scipy import ndimage
dens = np.clip(0.55 * tex(3.0, 0.13) + 0.45 * tex(1.3, 0.61), 0, 1)          # cloud density: darker where thick
dens = ndimage.gaussian_filter(dens, 6.0) * np.clip(dz * 3.0, 0, 1)            # soft billows, none at the horizon (no aliasing)
t = np.clip(dz, 0, 1)
hz = np.clip(1 - t * 4, 0, 1)[..., None]
def sky(top, bottom, dark, glow=None):
    base = top + (bottom - top) * hz
    img = base * (1 - dark * dens[..., None] * np.clip(t * 6, 0, 1)[..., None])
    if glow is not None: img = img + glow * (np.clip(1 - t * 8, 0, 1) ** 2)[..., None]
    fade = np.clip((H / 2 - ys) / 12.0, 0, 1)[..., None]; low = img[H // 2 - 6].mean(0)
    return img * fade + low * (1 - fade)
day = sky(np.array([0.50, 0.53, 0.57]), np.array([0.70, 0.72, 0.74]), 0.28)
night = sky(np.array([0.035, 0.038, 0.048]), np.array([0.06, 0.062, 0.07]), 0.4, glow=np.array([0.07, 0.045, 0.025]))   # town glow under the deck
for img, nm in ((day, 'sky_rain.png'), (night, 'sky_rain_night.png')):
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save('%s/%s' % (OUT, nm)); print(nm)
