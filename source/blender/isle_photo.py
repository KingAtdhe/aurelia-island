"""Photo-scanned CC0 materials (ambientCG, via the CC0-Public-Domain-Textures collection), decoded to raw RGBA in photo/.
Colour maps are normalised to a neutral mean so the existing vertex colours keep deciding the hue of each surface."""
import os
import numpy as np
import isle_lib as L
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photo')


def raw(name, kind):
    f = os.path.join(D, '%s_%s.raw' % (name, kind))
    if not os.path.exists(f): return None
    a = np.fromfile(f, np.uint8); n = int(round((len(a) / 4) ** 0.5)); a = a.reshape(n, n, 4).astype(float) / 255.0
    if kind in ('Color', 'NormalGL', 'Roughness'):
        import isle_hd; a = isle_hd.upres(name, kind, a)                     # 1024 px rebuild with synthesised fine detail
    return a[::-1]


def colour(name, mean=0.82, keep=0.55):
    """Detail map: the photo divided by its average colour, so it adds texture and some of its own colour variation (keep) without its tint."""
    a = raw(name, 'Color')
    if a is None: return None
    c = a[..., :3] ** 2.2; m = c.reshape(-1, 3).mean(0); l = c.mean(2, keepdims=True)
    tint = c / np.maximum(m, 1e-3) * m.mean(); c = l + (tint - l) * keep
    c = c / c.mean() * mean; return np.clip(c, 0, 1) ** (1 / 2.2)


def images(T, prefix):
    """Replace entries of the texture dict T: key -> (photo name, normal strength scale)."""
    MAP = dict(asphalt='Asphalt010', detail='Grass004', forest='Ground048', field='Ground003', rock='Rock051', sand='Ground080', snow='Snow004', pave='PavingStones070', gravel='Gravel022',
               plaster='Plaster003', roof='RoofingTiles006', boulder='Rock046S', bark='Bark007')
    used = []
    for key, nm in MAP.items():
        if key not in prefix: continue
        c = colour(nm, dict(asphalt=0.3, rock=0.6, gravel=0.66, boulder=0.66, pave=0.72).get(key, 0.8))
        if c is None: continue
        T[key] = L.make_image('photo_' + nm, c); n = raw(nm, 'NormalGL')
        if n is not None: T[key + '_n'] = L.make_image('photo_' + nm + '_n', n[..., :3], raw=True)
        r = raw(nm, 'Roughness')
        if r is not None and key == 'asphalt': T['asphalt_orm'] = L.make_image('photo_' + nm + '_orm', np.dstack([np.ones(r.shape[:2]), np.clip(r[..., 0] * 0.35 + 0.62, 0.72, 1), np.zeros(r.shape[:2])]), raw=True)
        used.append(nm)
    L.STATS['photo_materials'] = sorted(set(L.STATS.get('photo_materials', []) + used))
    return T
