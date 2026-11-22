import bpy, numpy as np
from PIL import Image
def load(n):
    im = bpy.data.images.load('/home/claude/bake/%s.exr' % n); w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, 0]; return a
sun, free, sky = load('sun'), load('sunfree'), load('sky')
vis = np.clip(sun / np.maximum(free, 1e-4), 0, 1); vis[free < 1e-3] = 1.0
ref = np.percentile(sky[sky > 0.05], 95) if (sky > 0.05).any() else 1.0
ao = np.clip(sky / ref, 0, 1)
out = np.stack([vis, ao, np.zeros_like(vis)], -1)
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save('/home/claude/bake/bake_coast.png')
Image.fromarray(((vis * 0.6 + ao * 0.4) * 255).astype(np.uint8)).save('/home/claude/bake/preview.png')
print('vis mean', vis.mean(), 'ao mean', ao.mean(), out.shape)
