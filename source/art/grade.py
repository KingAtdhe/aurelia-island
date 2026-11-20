"""Production grade for concept renders: highlight bloom, gentle S-curve, warm highlights / cool shadows, light vignette, unsharp."""
import numpy as np
from PIL import Image, ImageFilter

def finish(src, dst, night=False):
    im = Image.open(src).convert('RGB'); a = np.asarray(im, np.float32) / 255.0
    l = a.mean(2, keepdims=True)
    br = np.clip((a - (0.55 if night else 0.78)) / 0.4, 0, 1)                                    # bloom from the bright parts
    g = np.asarray(Image.fromarray((br * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(a.shape[1] / 90)), np.float32) / 255.0
    a = a + g * (0.55 if night else 0.25)
    t = np.clip((l - 0.15) / 0.7, 0, 1)
    warm, cool = (np.array([1.05, 1.0, 0.92]), np.array([0.95, 1.0, 1.07])) if not night else (np.array([1.08, 0.98, 0.86]), np.array([0.9, 0.97, 1.1]))
    a = a * (cool * (1 - t) + warm * t)
    a = np.clip(a, 0, 1); a = a * a * (3 - 2 * a) * 0.25 + a * 0.75                           # gentle S-curve
    H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]; v = 1 - 0.1 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.5
    a = np.clip(a * v[..., None], 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))
    out.save(dst, quality=94)
