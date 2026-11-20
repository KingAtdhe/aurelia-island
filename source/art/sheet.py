"""Aurelia Island art sheets: building elevations and shopfront signage, drawn to scale with the game's photo materials."""
import math, random

S = 24.0                      # px per metre (sheet 01)
K = S / 13.0
random.seed(7)
DEFS = []
_pat = set()


def pat(name, tile_m):
    pid = 'p_%s_%d' % (name.replace('#', ''), int(tile_m * 10))
    if pid not in _pat:
        _pat.add(pid); w = tile_m * S
        DEFS.append(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{w:.1f}" height="{w:.1f}"><image href="file:///tmp/{name}.jpg" width="{w:.1f}" height="{w:.1f}" preserveAspectRatio="none"/></pattern>')
    return pid


_tinted = {}
def tinted(name, tint, op):
    """Material photo multiplied by a tint once, saved as its own swatch image."""
    key = (name, tint, round(op, 2))
    if key not in _tinted:
        from PIL import Image
        import numpy as np
        a = np.asarray(Image.open(f'/tmp/sheet_{name}.jpg').convert('RGB'), float) / 255.0
        if tint:
            c = np.array([int(tint[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
            a = a * (1 - op + op * c)
        fn = f'sw_{name}_{(tint or "n").strip("#")}_{int(op * 100)}'
        Image.fromarray((np.clip(a, 0, 1) * 255).astype('uint8')).save(f'/tmp/{fn}.jpg', quality=90); _tinted[key] = fn
    return _tinted[key]


def wall(x, y, w, h, name, tile, tint=None, op=0.55):
    """Photo material rectangle, optionally tinted (multiply, baked into the swatch)."""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#{pat(tinted(name, tint, op), tile)})"/>'


def rect(x, y, w, h, fill, extra=''):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" {extra}/>'


def shadow(x, y, w, h, op=0.28):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#sh)" opacity="{op}"/>'


def window(x, y, w, h, frame='#f2efe6', kind=None, cross=True, sill='stone', lintel=True, shutters=None):
    """Recessed window: reveal shadow, sky-reflecting glass, frame and glazing bars, stone sill and lintel, curtain or blind."""
    o = []
    if shutters:
        for sx in (x - w * 0.52, x + w * 1.02):
            o.append(rect(sx, y, w * 0.5, h, shutters, 'stroke="#00000033" stroke-width="1"'))
            for k in range(1, int(h / 5)): o.append(f'<line x1="{sx + 2:.1f}" y1="{y + k * 5:.1f}" x2="{sx + w * 0.5 - 2:.1f}" y2="{y + k * 5:.1f}" stroke="#0000002a" stroke-width="1.2"/>')
    o.append(rect(x - 1.5, y - 1.5, w + 3, h + 3, '#00000055'))
    o.append(rect(x, y, w, h, 'url(#glass)'))
    k = kind if kind is not None else random.choice(['clear', 'curtain', 'blind', 'dark', 'clear', 'lit'])
    if k == 'curtain':
        c = random.choice(['#b9a37e', '#8a5a4a', '#d8d2c2', '#6c7f8c'])
        o.append(rect(x, y, w * 0.26, h, c, 'opacity="0.85"')); o.append(rect(x + w * 0.74, y, w * 0.26, h, c, 'opacity="0.85"'))
    elif k == 'blind':
        bh = h * random.uniform(0.25, 0.7); o.append(rect(x, y, w, bh, '#e6e2d6', 'opacity="0.95"'))
        for j in range(int(bh / 3)): o.append(f'<line x1="{x:.1f}" y1="{y + j * 3:.1f}" x2="{x + w:.1f}" y2="{y + j * 3:.1f}" stroke="#00000018" stroke-width="1"/>')
    elif k == 'dark': o.append(rect(x, y, w, h, '#0b1520', 'opacity="0.55"'))
    elif k == 'lit': o.append(rect(x, y + h * 0.35, w, h * 0.65, '#ffcf8a', 'opacity="0.22"'))
    o.append(rect(x, y, w, 3.5, '#00000060'))                                          # head reveal shadow
    o.append(rect(x, y, 3, h, '#00000040'))
    o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{frame}" stroke-width="3"/>')
    if cross:
        o.append(rect(x + w / 2 - 1.3, y, 2.6, h, frame)); o.append(rect(x, y + h * 0.32 - 1.2, w, 2.4, frame))
    if sill:
        o.append(wall(x - 4, y + h, w + 8, 5, 'Bricks076A', 1.2, '#ece6d8', 0.5)); o.append(shadow(x - 4, y + h + 5, w + 8, 5, 0.35))
    if lintel: o.append(wall(x - 3, y - 6, w + 6, 6, 'Bricks076A', 1.2, '#efe9dc', 0.45))
    return ''.join(o)


def balcony(x, y, w):
    o = [wall(x - 6, y, w + 12, 5, 'Concrete044A', 2, '#ddd8cc', 0.4), shadow(x - 6, y + 5, w + 12, 6, 0.4)]
    o.append(rect(x - 6, y - 14, w + 12, 2, '#262a2e'))
    for k in range(int((w + 12) / 5) + 1): o.append(rect(x - 6 + k * 5, y - 14, 1.2, 14, '#262a2e'))
    return ''.join(o)


def text(x, y, s, size, fill, family='Inter', weight=700, anchor='middle', ls=0, extra=''):
    s = str(s).replace('&', '&amp;')
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{s}</text>'


def dim(x0, y0, x1, y1, label, vertical=False):
    if vertical:
        return (f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#555" stroke-width="1"/><line x1="{x0 - 5}" y1="{y0}" x2="{x0 + 5}" y2="{y0}" stroke="#555"/><line x1="{x0 - 5}" y1="{y1}" x2="{x0 + 5}" y2="{y1}" stroke="#555"/>'
                + text(x0 - 8, (y0 + y1) / 2, label, 12, '#444', weight=500, anchor='end'))
    return (f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#555" stroke-width="1"/><line x1="{x0}" y1="{y0 - 5}" x2="{x0}" y2="{y0 + 5}" stroke="#555"/><line x1="{x1}" y1="{y0 - 5}" x2="{x1}" y2="{y0 + 5}" stroke="#555"/>'
            + text((x0 + x1) / 2, y0 + 16, label, 12, '#444', weight=500))


def awning(x, y, w, c1, c2, label=None, lc='#fff', font='Inter'):
    o = [f'<path d="M{x - 6:.1f},{y:.1f} L{x + w + 6:.1f},{y:.1f} L{x + w + 14:.1f},{y + 26:.1f} L{x - 14:.1f},{y + 26:.1f} Z" fill="{c1}"/>']
    n = int((w + 28) / 14)
    for k in range(0, n, 2):
        xa = x - 14 + k * (w + 28) / n; xb = xa + (w + 28) / n
        o.append(f'<path d="M{xa + (x - 6 - (x - 14)) * (1 - 0):.1f},{y:.1f} L{xb:.1f},{y:.1f} L{xb:.1f},{y + 26:.1f} L{xa:.1f},{y + 26:.1f} Z" fill="{c2}" opacity="0.9"/>')
    o.append(f'<path d="M{x - 14:.1f},{y + 26:.1f} ' + ' '.join(f'Q{x - 14 + (k + 0.5) * (w + 28) / 8:.1f},{y + 36:.1f} {x - 14 + (k + 1) * (w + 28) / 8:.1f},{y + 26:.1f}' for k in range(8)) + f' Z" fill="{c1}"/>')
    o.append(shadow(x - 10, y + 30, w + 20, 16, 0.35))
    if label: o.append(text(x + w / 2, y + 22, label, 11 * K * 0.8, lc, font, 700, ls=2))
    return ''.join(o)


def shopfront(x, y, w, h, frame, sign, signbg, signfg, font, fweight=700, fsize=None, style='flat', awn=None, goods=None, blade=None):
    """Ground-floor shop: fascia sign, display windows with goods, door, stall riser."""
    o = [rect(x, y, w, h, frame)]
    fh = 0.9 * S; o.append(rect(x + 6, y + 6, w - 12, fh, signbg)); o.append(shadow(x + 6, y + 6 + fh, w - 12, 6, 0.3))
    fsz = min((fsize * K) if fsize else 99, fh * 0.62, (w - 30) / max(4, len(sign)) * 1.5)
    if style == 'gold': o.append(f'<rect x="{x + 10:.1f}" y="{y + 10:.1f}" width="{w - 20:.1f}" height="{fh - 8:.1f}" fill="none" stroke="#d4af5a" stroke-width="1.5"/>')
    o.append(text(x + w / 2, y + 6 + fh * 0.68, sign, round(fsz, 1), signfg, font, fweight, ls=1.5))
    gy = y + fh + 18; gh = h - fh - 18 - 0.55 * S; dw = 1.25 * S
    o.append(rect(x + 8, gy, w - 16, gh, 'url(#glassShop)'))
    dx = x + w * 0.62
    o.append(rect(dx, gy, dw, gh + 0.55 * S, '#1b2026')); o.append(rect(dx + 4, gy + 4, dw - 8, gh - 6, 'url(#glassShop)')); o.append(rect(dx + dw - 9, gy + gh * 0.5, 3, 16, '#c9c2b0'))
    if goods: o.append(goods(x + 14, gy + gh - 4, dx - x - 24))
    o.append(rect(x + 8, gy, w - 16, 3, frame)); o.append(rect(x + w * 0.31, gy, 3, gh, frame))
    o.append(wall(x + 8, gy + gh, dx - x - 8, 0.55 * S, 'Bricks066', 2, '#bdb6a8', 0.4)); o.append(wall(dx + dw, gy + gh, x + w - 8 - dx - dw, 0.55 * S, 'Bricks066', 2, '#bdb6a8', 0.4))
    if awn: o.append(awning(x + 10, gy - 8, w - 20, *awn))
    if blade:
        bx = x + w - 0.75 * S - 14; by = y - 2.4 * S
        o.append(rect(bx, by + 6, 0.9 * S, 2, '#2b2b2b')); o.append(rect(bx + 4, by, 0.75 * S, 1.9 * S, blade[1], 'rx="3"'))
        o.append(text(bx + 4 + 0.375 * S, by + 0.95 * S + 5, blade[0], 13 * K, blade[2], font, 800))
    return ''.join(o)


def goods_bread(x, y, w):
    o = []
    for k in range(int(w / 16)):
        cx = x + 8 + k * 16; o.append(f'<ellipse cx="{cx:.1f}" cy="{y - 8:.1f}" rx="7" ry="4.5" fill="#c58b45"/><ellipse cx="{cx + 4:.1f}" cy="{y - 17:.1f}" rx="6" ry="4" fill="#d9a35c"/>')
    o.append(rect(x, y - 4, w, 4, '#6b4a2f')); return ''.join(o)


def goods_books(x, y, w):
    o = []; cols = ['#7a2e2e', '#2f4f6f', '#c9a24a', '#3d5c3a', '#e3ddd0', '#5a3a5f']
    for sh in (0, 1):
        xx = x
        while xx < x + w - 6:
            bw = random.uniform(3, 6); bh = random.uniform(11, 17); o.append(rect(xx, y - 4 - sh * 22 - bh, bw, bh, random.choice(cols))); xx += bw + 0.6
        o.append(rect(x, y - 4 - sh * 22, w, 2.5, '#4a3626'))
    return ''.join(o)


def goods_flowers(x, y, w):
    o = []
    for k in range(int(w / 12)):
        cx = x + 6 + k * 12; o.append(rect(cx - 4, y - 12, 8, 12, '#7a5236'))
        for j in range(5): o.append(f'<circle cx="{cx + random.uniform(-5, 5):.1f}" cy="{y - 15 - random.uniform(0, 9):.1f}" r="3" fill="{random.choice(["#e0405a", "#f2c230", "#ffffff", "#b05ad0", "#ff8a3c"])}"/>')
    return ''.join(o)


def goods_pharm(x, y, w):
    o = []
    for sh in (0, 1):
        for k in range(int(w / 9)): o.append(rect(x + 2 + k * 9, y - 12 - sh * 20, 6, 10, random.choice(['#ffffff', '#e8f2f0', '#4fae7a', '#2f7fbf'])))
        o.append(rect(x, y - 2 - sh * 20, w, 2, '#d8dcdc'))
    return ''.join(o)


def goods_cafe(x, y, w):
    o = [rect(x, y - 14, w, 14, '#3a2a20')]
    for k in range(int(w / 14)): o.append(f'<path d="M{x + 4 + k * 14:.1f},{y - 22:.1f} l8,0 l-1,8 l-6,0 Z" fill="#f4f1ea"/>')
    return ''.join(o)


def building_A(X, G):
    """Corner apartment block: red brick, 6 storeys, stone cornice, iron balconies, cafe and bakery at street level."""
    W = 22 * S; gf = 4.6 * S; fl = 3.2 * S; n = 5; H = gf + n * fl
    o = [wall(X, G - H, W, H, 'Bricks085', 2.2, '#f2d9cc', 0.25)]
    o.append(wall(X, G - gf, W, gf, 'Bricks066', 2.4, '#d9d2c4', 0.45))                                 # stone ground floor
    o.append(wall(X - 4, G - gf - 0.5 * S, W + 8, 0.5 * S, 'Bricks076A', 1.4, '#efe9dc', 0.4)); o.append(shadow(X - 4, G - gf, W + 8, 8, 0.4))
    o.append(shopfront(X + 0.6 * S, G - gf + 0.4 * S, 10 * S, gf - 0.4 * S, '#1f3d2f', 'CAFFÈ MARINA', '#1f3d2f', '#f1e3c2', 'Lora', 700, 19, 'gold', ('#1f3d2f', '#efe6d2', None), goods_cafe, ('C', '#1f3d2f', '#f1e3c2')))
    o.append(shopfront(X + 11.4 * S, G - gf + 0.4 * S, 10 * S, gf - 0.4 * S, '#6b2c1f', 'Panificio Rossi', '#efe4cf', '#6b2c1f', 'Lora', 700, 20, 'flat', ('#a8342a', '#f4efe2', None), goods_bread))
    for f in range(n):
        y = G - gf - (f + 1) * fl + 0.55 * S
        for b in range(6):
            x = X + 1.2 * S + b * 3.55 * S
            o.append(window(x, y, 1.45 * S, 1.95 * S, '#f2efe6', None))
        if f in (1, 3): o.append(balcony(X + 1.2 * S - 4, y + 1.95 * S + 6, 3.55 * S * 2 - 1.9 * S))
        if f in (1, 3): o.append(balcony(X + 1.2 * S + 4 * 3.55 * S - 4, y + 1.95 * S + 6, 3.55 * S * 2 - 1.9 * S))
        o.append(wall(X, G - gf - f * fl - 0.18 * S, W, 0.18 * S, 'Bricks076A', 1.2, '#e9e2d4', 0.4))          # string course
    o.append(wall(X - 6, G - H - 0.9 * S, W + 12, 0.9 * S, 'Bricks076A', 1.6, '#efe9dc', 0.35)); o.append(shadow(X - 6, G - H, W + 12, 12, 0.45))
    for k in range(23): o.append(rect(X - 4 + k * (W + 8) / 23, G - H - 0.25 * S, 5, 0.25 * S, '#d8d0c0'))   # dentils
    o.append(wall(X + W * 0.62, G - H - 3.2 * S, 2.6 * S, 2.3 * S, 'Wood049', 1.5, '#8a6a4a', 0.5))          # rooftop water tank
    o.append(rect(X + W * 0.62 - 3, G - H - 0.9 * S - 6, 3, 6, '#333')); o.append(f'<path d="M{X + W * 0.62 - 4:.1f},{G - H - 3.2 * S:.1f} l{2.6 * S / 2 + 4:.1f},-14 l{2.6 * S / 2 + 4:.1f},14 Z" fill="#4a4f55"/>')
    for k in range(2): o.append(rect(X + W * 0.2 + k * 30, G - H - 1.6 * S, 22, 0.7 * S, '#c9ccce', 'stroke="#888" stroke-width="1"'))   # AC units on the roof
    o.append(rect(X + W - 10, G - H, 4, H, '#5d6166')); o.append(rect(X + W - 12, G - H + 4, 8, 6, '#5d6166'))          # drainpipe
    return ''.join(o), W, H


def building_B(X, G):
    """Art-deco office: cream ashlar, vertical piers, bronze spandrels, stepped crown, gilded lettering over a canopied entrance."""
    W = 24 * S; gf = 5.2 * S; fl = 3.6 * S; n = 7; H = gf + n * fl
    o = [wall(X, G - H, W, H, 'Bricks066', 2.6, '#f2dfb8', 0.75)]
    bays = 6; bw = (W - 2.4 * S) / bays
    for f in range(n):
        y = G - gf - (f + 1) * fl
        for b in range(bays):
            x = X + 1.2 * S + b * bw + 0.5 * S
            o.append(window(x, y + 0.35 * S, bw - 1.0 * S, fl - 1.3 * S, '#3b3a35', random.choice(['clear', 'blind', 'lit', 'dark']), cross=False, sill=None, lintel=False))
            o.append(rect(x + (bw - 1.0 * S) / 3, y + 0.35 * S, 2, fl - 1.3 * S, '#3b3a35')); o.append(rect(x + 2 * (bw - 1.0 * S) / 3, y + 0.35 * S, 2, fl - 1.3 * S, '#3b3a35'))
            sp = y + fl - 0.95 * S; o.append(rect(x, sp, bw - 1.0 * S, 0.8 * S, '#6b5434'))                       # bronze spandrel
            for k in range(5): o.append(rect(x + 4 + k * (bw - 1.0 * S - 8) / 5, sp + 3, (bw - 1.0 * S - 8) / 5 - 3, 0.8 * S - 6, '#8a6d42'))
    for b in range(bays + 1):
        x = X + 1.2 * S + b * bw - 0.25 * S
        o.append(wall(x, G - H - (1.6 * S if b in (2, 4) else 0), 0.5 * S + (0 if b % bays else 0), H - gf + (1.6 * S if b in (2, 4) else 0), 'Plaster004', 3, '#fbf3e2', 0.2)); o.append(rect(x + 0.5 * S, G - H, 4, H - gf, '#00000022'))
    for k, (cx, cw, ch) in enumerate([(W / 2, W * 0.42, 2.4 * S), (W / 2, W * 0.24, 4.6 * S), (W / 2, W * 0.1, 6.4 * S)]):   # stepped crown
        o.append(wall(X + cx - cw / 2, G - H - ch, cw, ch, 'Bricks066', 2.6, '#f2dfb8', 0.75)); o.append(shadow(X + cx - cw / 2, G - H - ch + ch, cw, 6, 0.3))
        o.append(rect(X + cx - cw / 2, G - H - ch, cw, 5, '#c9a45c'))
    o.append(rect(X + W / 2 - 1, G - H - 9.5 * S, 2, 3.1 * S, '#8b8b8b'))
    o.append(wall(X, G - gf, W, gf, 'Bricks076A', 2.2, '#cfc6b4', 0.4))
    o.append(rect(X + W / 2 - 4 * S, G - gf + 1.2 * S, 8 * S, gf - 1.2 * S, '#2a2620'))                              # entrance
    o.append(rect(X + W / 2 - 3.6 * S, G - gf + 1.6 * S, 7.2 * S, gf - 1.6 * S, 'url(#glassShop)'))
    for k in range(4): o.append(rect(X + W / 2 - 3.6 * S + k * 2.4 * S, G - gf + 1.6 * S, 3, gf - 1.6 * S, '#c9a45c'))
    o.append(rect(X + W / 2 - 5 * S, G - gf + 1.0 * S, 10 * S, 0.45 * S, '#2a2620')); o.append(shadow(X + W / 2 - 5 * S, G - gf + 1.45 * S, 10 * S, 14, 0.5))
    o.append(rect(X + W * 0.14, G - gf + 0.05 * S, W * 0.72, 0.9 * S, '#2a2620')); o.append(rect(X + W * 0.14 + 4, G - gf + 0.05 * S + 4, W * 0.72 - 8, 0.9 * S - 8, 'none', 'stroke="#c9a45c" stroke-width="1.5"'))
    o.append(text(X + W / 2, G - gf + 0.72 * S, 'AURELIA  INSURANCE', 17 * K, '#c9a45c', 'GFS Baskerville', 700, ls=5))
    for side in (-1, 1):
        x = X + W / 2 + side * 7.5 * S - 2.5 * S
        o.append(window(x, G - gf + 0.9 * S, 5 * S, gf - 1.9 * S, '#3b3a35', 'lit', cross=False, sill='stone', lintel=False))
    return ''.join(o), W, H


def building_C(X, G):
    """Modern office: blue-green glass curtain wall, aluminium mullions, concrete floor bands, double-height lobby, rooftop plant screen."""
    W = 26 * S; gf = 7.0 * S; fl = 3.8 * S; n = 9; H = gf + n * fl
    o = [rect(X, G - H, W, H - gf, 'url(#curtain)')]
    for f in range(n + 1):
        y = G - gf - f * fl; o.append(wall(X, y - 0.55 * S, W, 0.55 * S, 'Concrete044A', 3, '#d6d6d2', 0.3))
    for b in range(14): o.append(rect(X + b * W / 13 - 1.5, G - H, 3, H - gf, '#9aa6ad'))
    for f in range(n):
        for b in range(13):
            if random.random() < 0.22: o.append(rect(X + b * W / 13 + 3, G - gf - (f + 1) * fl + 4, W / 13 - 6, fl - 0.55 * S - 8, '#ffffff', 'opacity="0.18"'))
            if random.random() < 0.18: o.append(rect(X + b * W / 13 + 3, G - gf - (f + 1) * fl + 4, W / 13 - 6, (fl - 0.55 * S - 8) * random.uniform(0.3, 0.8), '#e4e7e6', 'opacity="0.55"'))
    o.append(f'<path d="M{X:.1f},{G - H:.1f} L{X + W * 0.55:.1f},{G - H:.1f} L{X:.1f},{G - gf - fl * 3:.1f} Z" fill="#ffffff" opacity="0.1"/>')          # sky reflection sweep
    o.append(wall(X + W * 0.15, G - H - 2.6 * S, W * 0.7, 2.6 * S, 'Metal032', 2, '#b9c0c4', 0.3))
    for k in range(40): o.append(rect(X + W * 0.15 + k * W * 0.7 / 40, G - H - 2.6 * S, 2, 2.6 * S, '#6d7479'))
    o.append(wall(X, G - gf, W, gf, 'Concrete044A', 3, '#cfcfca', 0.3))
    o.append(rect(X + 1.5 * S, G - gf + 1.0 * S, W - 3 * S, gf - 1.0 * S, 'url(#glassShop)'))
    for k in range(9): o.append(rect(X + 1.5 * S + k * (W - 3 * S) / 8, G - gf + 1.0 * S, 3, gf - 1.0 * S, '#7d868c'))
    o.append(text(X + W / 2, G - gf + 0.78 * S, 'N O R D A', 22 * K, '#16302b', 'Inter', 800, ls=4))
    o.append(rect(X + W / 2 - 4 * S, G - gf + 0.92 * S, 8 * S, 2, '#2fb38a'))
    return ''.join(o), W, H


def building_D(X, G):
    """Row of three townhouses: coloured plaster, green shutters, tiled roofs with dormers; barber, pharmacy and florist below."""
    o = []; Wt = 7.4 * S; gf = 4.2 * S; fl = 3.1 * S; n = 3
    specs = [('#c8714f', 'BARBIERE', '#1d2b4a', '#f3ead9', 'Inter', ('#1d2b4a', '#f3ead9', None), None, 'barber'),
             ('#d9ad55', 'FARMACIA', '#f4f6f4', '#1c7a4c', 'Inter', None, goods_pharm, 'pharm'),
             ('#9fb6c4', 'Fiori di Lucia', '#3c5a3a', '#f6efe0', 'Lora', ('#3c5a3a', '#f2eadb', None), goods_flowers, None)]
    H = gf + n * fl
    for i, (col, sign, sbg, sfg, font, awn, goods, extra) in enumerate(specs):
        x0 = X + i * Wt; h_ = H + (0.6 * S if i == 1 else 0)
        o.append(wall(x0, G - h_, Wt, h_, 'Plaster004', 3, col, 0.85))
        o.append(shopfront(x0 + 0.4 * S, G - gf + 0.3 * S, Wt - 0.8 * S, gf - 0.3 * S, '#2b2b2b' if i == 0 else ('#1c7a4c' if i == 1 else '#3c5a3a'), sign, sbg, sfg, font, 800 if i < 2 else 700, 18 if i < 2 else 19, 'flat', awn, goods,
                            ('✚', '#1c9a5c', '#ffffff') if i == 1 else None))
        if extra == 'barber':
            px = x0 + Wt - 0.7 * S; o.append(rect(px, G - gf + 0.9 * S, 10, 2.2 * S, '#ffffff', 'rx="4"'))
            for k in range(6): o.append(f'<path d="M{px:.1f},{G - gf + 0.9 * S + k * 5 + 2:.1f} l10,-6 l0,3 l-10,6 Z" fill="{["#c62828", "#1d3f8a"][k % 2]}"/>')
        for f in range(n):
            y = G - gf - (f + 1) * fl + 0.5 * S
            for b in range(2):
                o.append(window(x0 + 1.6 * S + b * 2.9 * S, y, 1.25 * S, 1.9 * S, '#f4f1ea', None, True, 'stone', False, '#2f5d3a'))
            if f == 0: o.append(balcony(x0 + 1.2 * S, y + 1.9 * S + 6, Wt - 2.4 * S))
        rx0 = x0 - 0.3 * S; rx1 = x0 + Wt + 0.3 * S; ry = G - h_
        o.append(f'<clipPath id="rf{i}"><path d="M{rx0:.1f},{ry:.1f} L{x0 + Wt * 0.5:.1f},{ry - 3.4 * S:.1f} L{rx1:.1f},{ry:.1f} Z"/></clipPath>')
        o.append(f'<g clip-path="url(#rf{i})">' + wall(rx0, ry - 3.4 * S, rx1 - rx0, 3.4 * S, 'RoofingTiles006', 1.8, '#c46a45', 0.45) + '</g>')
        o.append(rect(rx0, ry - 3, rx1 - rx0, 5, '#efe9dc')); o.append(shadow(x0, ry + 2, Wt, 10, 0.4))
        dx = x0 + Wt / 2 - 0.8 * S; o.append(wall(dx, ry - 2.4 * S, 1.6 * S, 1.5 * S, 'Plaster004', 3, col, 0.85))     # dormer
        o.append(window(dx + 0.35 * S, ry - 2.2 * S, 0.9 * S, 1.05 * S, '#f4f1ea', None, True, None, False))
        o.append(f'<path d="M{dx - 4:.1f},{ry - 2.4 * S:.1f} L{dx + 0.8 * S:.1f},{ry - 3.2 * S:.1f} L{dx + 1.6 * S + 4:.1f},{ry - 2.4 * S:.1f} Z" fill="#8e4a32"/>')
        if i != 1: o.append(wall(x0 + Wt * 0.78, ry - 3.0 * S, 0.7 * S, 1.6 * S, 'Bricks085', 1.2, '#e9c7b5', 0.3))   # chimney
    return ''.join(o), 3 * Wt, H + 3.4 * S


def common_defs():
    return '''<linearGradient id="glass" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="#9ab8cf"/><stop offset="0.45" stop-color="#4c6a82"/><stop offset="1" stop-color="#1c2a36"/></linearGradient>
<linearGradient id="glassShop" x1="0" y1="0" x2="0.2" y2="1"><stop offset="0" stop-color="#5d7a8c"/><stop offset="0.5" stop-color="#2b3d4b"/><stop offset="1" stop-color="#18222b"/></linearGradient>
<linearGradient id="curtain" x1="0" y1="0" x2="0.5" y2="1"><stop offset="0" stop-color="#8fb9c4"/><stop offset="0.5" stop-color="#3f6d7b"/><stop offset="1" stop-color="#20414c"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="1"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>
<linearGradient id="shopLit" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe2b0"/><stop offset="1" stop-color="#c98a3e"/></linearGradient>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9eef2"/><stop offset="1" stop-color="#f7f6f2"/></linearGradient>'''


def swatch(x, y, name, tint, op, label):
    return wall(x, y, 70, 70, name, 70 / S, tint, op) + f'<rect x="{x}" y="{y}" width="70" height="70" fill="none" stroke="#999"/>' + text(x + 35, y + 86, label, 11, '#333', weight=500)


def sheet1():
    body = []; Wd, Ht = 2900, 1720; G = 1330
    body.append(rect(0, 0, Wd, Ht, 'url(#sky)'))
    body.append(text(60, 70, 'AURELIA ISLAND — CITY ART SHEET 01', 34, '#1d2a33', 'Inter', 800, 'start', 1))
    body.append(text(60, 102, 'Building designs · front elevations to scale (1 m = 24 px) · materials are the photo textures used in the game', 16, '#55606a', 'Inter', 500, 'start'))
    x = 80; labels = []
    for fn, title, sub in ((building_A, 'A · Corner apartment block', '6 storeys · red brick, stone ground floor & cornice · iron balconies · café + bakery'),
                           (building_B, 'B · Art-deco office', '8 storeys · cream ashlar piers, bronze spandrels, stepped crown · gilded lettering'),
                           (building_C, 'C · Modern glass office', '10 storeys · blue-green curtain wall, concrete floor bands · double-height lobby'),
                           (building_D, 'D · Townhouse row (3 houses)', '4 storeys + dormers · coloured plaster, green shutters, clay tiles · barber, pharmacy, florist')):
        s, w, h = fn(x, G); body.append(s)
        body.append(dim(x, G + 22, x + w, None, f'{w / S:.0f} m'))
        body.append(dim(x - 18, G - h, None, G, f'{h / S:.0f} m', vertical=True))
        body.append(text(x, G + 66, title, 19, '#1d2a33', 'Inter', 800, 'start')); body.append(text(x, G + 86, sub, 12.5, '#55606a', 'Inter', 500, 'start'))
        x += w + 90
    body.append(rect(0, G, Wd, 6, '#8c8c86'))
    sx = 60; sy = 1560
    body.append(text(sx, sy - 14, 'MATERIALS', 14, '#1d2a33', 'Inter', 800, 'start', 2))
    for i, (n, t, o, l) in enumerate([('Bricks085', None, 0, 'Red brick'), ('Bricks023', None, 0, 'Brown brick'), ('Bricks029', None, 0, 'Cream brick'), ('Bricks061', None, 0, 'Painted brick'), ('Bricks066', '#f4ead6', 0.35, 'Ashlar'),
                                      ('Bricks076A', '#efe9dc', 0.4, 'Stone trim'), ('Plaster004', '#c8714f', 0.85, 'Plaster (tinted)'), ('Concrete044A', None, 0, 'Concrete'), ('RoofingTiles006', '#c46a45', 0.45, 'Clay tiles'), ('Metal032', None, 0, 'Metal screen')]):
        body.append(swatch(sx + i * 92, sy, n, t, o, l))
    px = 1080
    body.append(text(px, sy - 14, 'PALETTE', 14, '#1d2a33', 'Inter', 800, 'start', 2))
    for i, (c, l) in enumerate([('#1f3d2f', 'Marina green'), ('#6b2c1f', 'Oxblood'), ('#c9a45c', 'Deco gold'), ('#6b5434', 'Bronze'), ('#3f6d7b', 'Curtain glass'), ('#c8714f', 'Terracotta'), ('#d9ad55', 'Ochre'), ('#9fb6c4', 'Harbour blue'), ('#2f5d3a', 'Shutter green'), ('#1d2b4a', 'Navy')]):
        body.append(rect(px + i * 72, sy, 60, 60, c, 'rx="6"')); body.append(text(px + i * 72 + 30, sy + 78, l, 10.5, '#333', weight=500))
    nx = 1880
    body.append(text(nx, sy - 14, 'MODELLING NOTES', 14, '#1d2a33', 'Inter', 800, 'start', 2))
    for i, l in enumerate(['Windows recessed 0.2 m with stone sills/lintels; glass shows the room-interior shader',
                           'Cornices, string courses, balconies, spandrels and piers modelled as real geometry',
                           'Signs are unique per shop (lettering, colours, materials), not one atlas repeated',
                           'Each design gets 3 colour variants so streets do not repeat; LOD versions for far view']):
        body.append(text(nx, sy + 8 + i * 22, '• ' + l, 12.5, '#333', 'Inter', 500, 'start'))
    return Wd, Ht, ''.join(body)


def sign_tile(x, y, w, h, title, d):
    """One shop design on sheet 02: day elevation plus night neon/backlit version."""
    o = [rect(x, y, w, h, '#ffffff', 'rx="10" stroke="#d6d6d0"')]
    o.append(text(x + 16, y + 30, title, 16, '#1d2a33', 'Inter', 800, 'start'))
    o.append(text(x + 16, y + 50, d['note'], 11.5, '#55606a', 'Inter', 500, 'start'))
    bx = x + 16; by = y + 66; bw = w * 0.6 - 24; bh = h - 82
    o.append(wall(bx, by, bw, bh, d['wall'][0], 2.4, d['wall'][1], d['wall'][2]))
    sf = shopfront(bx + 12, by + bh * 0.22, bw - 24, bh * 0.78, d['frame'], d['sign'], d['sbg'], d['sfg'], d['font'], d.get('fw', 800), d.get('fs'), d.get('style', 'flat'), d.get('awn'), d.get('goods'), d.get('blade'))
    o.append(sf)
    nx = x + w * 0.6; nw = w * 0.4 - 16
    o.append(rect(nx, by, nw, bh, '#0d1420', 'rx="6"'))
    o.append(text(nx + nw / 2, by + 22, 'NIGHT', 10, '#7d8ca0', 'Inter', 700, ls=3))
    nc = d['neon']; fsz = min(30, (nw - 20) / max(4, len(d['sign'])) * 1.6)
    o.append(f'<text x="{nx + nw / 2:.1f}" y="{by + bh * 0.45:.1f}" font-family="{d["font"]}" font-size="{fsz:.1f}" font-weight="{d.get("fw", 800)}" fill="none" stroke="{nc}" stroke-width="5" opacity="0.35" text-anchor="middle" filter="url(#glow)">{d["sign"]}</text>')
    o.append(text(nx + nw / 2, by + bh * 0.45, d['sign'], round(fsz, 1), '#ffffff', d['font'], d.get('fw', 800), extra=f'filter="url(#glow)" style="fill:{nc}"'))
    o.append(rect(nx + 14, by + bh * 0.58, nw - 28, bh * 0.34, '#1a1712'))
    o.append(f'<rect x="{nx + 18:.1f}" y="{by + bh * 0.6:.1f}" width="{nw - 36:.1f}" height="{bh * 0.3:.1f}" fill="url(#shopLit)"/>')
    o.append(rect(nx + nw * 0.62, by + bh * 0.6, 3, bh * 0.3, '#1a1712')); o.append(rect(nx + nw * 0.35, by + bh * 0.6, 3, bh * 0.3, '#1a1712'))
    o.append(f'<ellipse cx="{nx + nw / 2:.1f}" cy="{by + bh * 0.93:.1f}" rx="{nw * 0.45:.1f}" ry="8" fill="#ffcf8a" opacity="0.18"/>')
    o.append(text(nx + nw / 2, by + bh - 12, d['nnote'], 10.5, '#9fb0c4', 'Inter', 500))
    return ''.join(o)


def sheet2():
    body = []; Wd, Ht = 2600, 1330
    DEFS.append('<filter id="glow" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    body.append(rect(0, 0, Wd, Ht, '#f3f2ee'))
    body.append(text(60, 70, 'AURELIA ISLAND — CITY ART SHEET 02', 34, '#1d2a33', 'Inter', 800, 'start', 1))
    body.append(text(60, 102, 'Shopfronts & signage · each shop has its own lettering, colours and night lighting · original names, no real brands', 16, '#55606a', 'Inter', 500, 'start'))
    D = [
        ('Caffè Marina', dict(note='Serif gold leaf on deep green · striped awning', wall=('Bricks085', '#f2d9cc', 0.25), frame='#1f3d2f', sign='CAFFÈ MARINA', sbg='#1f3d2f', sfg='#f1e3c2', font='Lora', fw=700, style='gold', awn=('#1f3d2f', '#efe6d2', None), goods=goods_cafe, blade=('C', '#1f3d2f', '#f1e3c2'), neon='#ffd27a', nnote='Warm backlit letters, lit interior')),
        ('Panificio Rossi', dict(note='Hand-painted script panel · red & cream awning', wall=('Bricks066', '#e7dccb', 0.35), frame='#6b2c1f', sign='Panificio Rossi', sbg='#efe4cf', sfg='#6b2c1f', font='Lora', fw=700, awn=('#a8342a', '#f4efe2', None), goods=goods_bread, neon='#ff9f6a', nnote='Spotlit sign, bread display glowing')),
        ('Farmacia', dict(note='Clean sans · green cross blade sign (animated at night)', wall=('Plaster004', '#d9ad55', 0.85), frame='#1c7a4c', sign='FARMACIA', sbg='#f4f6f4', sfg='#1c7a4c', font='Inter', blade=('✚', '#1c9a5c', '#ffffff'), goods=goods_pharm, neon='#37e08a', nnote='Green LED cross pulses')),
        ('Libreria Ponte', dict(note='Navy fascia, cream small caps · book display', wall=('Bricks023', None, 0), frame='#1d2b4a', sign='LIBRERIA PONTE', sbg='#1d2b4a', sfg='#efe6d2', font='GFS Baskerville', fw=700, goods=goods_books, awn=('#1d2b4a', '#e9e2d0', None), neon='#9cc7ff', nnote='Cool white halo lettering')),
        ('Fiori di Lucia', dict(note='Sage green, italic serif · flower buckets outside', wall=('Plaster004', '#9fb6c4', 0.85), frame='#3c5a3a', sign='Fiori di Lucia', sbg='#3c5a3a', sfg='#f6efe0', font='Lora', fw=700, goods=goods_flowers, awn=('#3c5a3a', '#f2eadb', None), neon='#ff8fc7', nnote='Pink neon script')),
        ('Barbiere 1962', dict(note='Navy & white, condensed caps · spinning barber pole', wall=('Plaster004', '#c8714f', 0.85), frame='#2b2b2b', sign='BARBIERE 1962', sbg='#1d2b4a', sfg='#f3ead9', font='Inter', awn=('#1d2b4a', '#f3ead9', None), neon='#ff4d5e', nnote='Red/blue neon, lit pole')),
        ('Hotel Coral', dict(note='Coral sign, gold border · canopy & flag', wall=('Bricks066', '#f4ead6', 0.35), frame='#7a2f2a', sign='HOTEL CORAL', sbg='#e06a5a', sfg='#fff6ec', font='GFS Baskerville', fw=700, style='gold', blade=('H', '#e06a5a', '#fff6ec'), neon='#ff7a6a', nnote='Coral neon, gold edge lighting')),
        ('Mare Bank', dict(note='Dark teal stone, brass letters, no awning', wall=('Bricks076A', '#d8d4c8', 0.4), frame='#14453f', sign='MARE BANK', sbg='#14453f', sfg='#d9c27a', font='Inter', fw=800, style='gold', neon='#e8d08a', nnote='Brass lettering, uplit facade')),
    ]
    tw, th = 615, 340
    for i, (title, d) in enumerate(D):
        x = 50 + (i % 4) * (tw + 20); y = 140 + (i // 4) * (th + 24)
        body.append(sign_tile(x, y, tw, th, title, d))
    y = 140 + 2 * (th + 24) + 10
    body.append(text(60, y + 10, 'ROOFTOP & BLADE SIGNS', 14, '#1d2a33', 'Inter', 800, 'start', 2))
    ads = [('AURELIA COLA', '#c0141e', '#fff7ef', 'Inter'), ('VORTEX MOTORS', '#121418', '#ff4a2a', 'Inter'), ('ISLAND AIR', '#1d5aa8', '#ffffff', 'Inter'), ('SUNSET RADIO 98.4', '#f07d1e', '#2a1a40', 'Inter'), ('GELATO BLU', '#5aa0e6', '#ffffff', 'Lora')]
    for i, (t, bg, fg, f) in enumerate(ads):
        x = 60 + i * 500; yy = y + 30
        body.append(rect(x, yy, 440, 170, bg, 'rx="4"')); body.append(rect(x + 8, yy + 8, 424, 154, 'none', f'stroke="{fg}" stroke-width="2" opacity="0.6"'))
        body.append(text(x + 220, yy + 100, t, 34 if len(t) < 13 else 26, fg, f, 800, ls=2))
        for k in range(3): body.append(rect(x + 60 + k * 150, yy + 170, 8, 50, '#555b60'))
        body.append(text(x + 220, yy + 245, 'Rooftop billboard on steel frame · lit by 4 lamps at night', 11, '#55606a', 'Inter', 500))
    return Wd, Ht, ''.join(body)


def render(fn, out):
    global DEFS
    DEFS = []; _pat.clear()
    w, h, body = fn()
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{common_defs()}{"".join(DEFS)}</defs>{body}</svg>'
    open(out, 'w').write(svg)
    return w, h


if __name__ == '__main__':
    import sys
    from playwright.sync_api import sync_playwright
    jobs = [(sheet1, '/tmp/art/sheet01.svg', '/tmp/art/art_sheet_01_buildings.png'), (sheet2, '/tmp/art/sheet02.svg', '/tmp/art/art_sheet_02_signs.png')]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        for fn, svg, png in jobs:
            w, h = render(fn, svg)
            pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
            html = svg.replace('.svg', '.html'); open(html, 'w').write('<html><body style="margin:0">' + open(svg).read() + '</body></html>')
            import time; t0 = time.time(); pg.goto('file://' + html); pg.wait_for_timeout(2000); pg.screenshot(path=png, timeout=240000, animations='disabled', caret='initial'); pg.close(); print('rendered', png, round(time.time() - t0, 1))
        b.close()
