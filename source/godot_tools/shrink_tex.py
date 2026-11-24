"""Shrink map textures to what the game imports anyway (colour 1024, normal/ORM 512): smaller repo, faster import."""
import os, sys
from PIL import Image
D = sys.argv[1]
for f in os.listdir(D):
    if not f.endswith(('.jpg', '.png')): continue
    nm = f.rsplit('.', 1)[0]; lim = 512 if (nm.endswith('_n') or '_n_' in nm or nm.endswith('_orm')) else 1024
    p = os.path.join(D, f); im = Image.open(p)
    if max(im.size) > lim:
        s = lim / max(im.size); im = im.resize((max(1, round(im.size[0] * s)), max(1, round(im.size[1] * s))), Image.LANCZOS)
        im.convert('RGB').save(p, quality=90) if f.endswith('.jpg') else im.save(p, optimize=True)
