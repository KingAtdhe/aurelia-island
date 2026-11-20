"""Lays the graded concept renders out as two presentation sheets (HTML rendered to PNG)."""
import os, sys
sys.path.insert(0, '/tmp/art')
import grade
from PIL import Image
F = '/tmp/hero/final'; G = '/tmp/art/g'; os.makedirs(G, exist_ok=True)
for n in ('street_day', 'A_day', 'B_day', 'C_day', 'D_day', 'street_night', 'A_night', 'D_night'):
    if os.path.exists(f'{F}/{n}.png'): grade.finish(f'{F}/{n}.png', f'{G}/{n}.jpg', 'night' in n)
el = Image.open('/tmp/art/art_sheet_01_buildings.png').convert('RGB')                     # elevation plans from sheet 01
for k, (x0, x1) in {'A': (40, 640), 'B': (660, 1300), 'C': (1330, 2030), 'D': (2040, 2660)}.items(): el.crop((x0, 260, x1, 1420)).save(f'{G}/el_{k}.jpg', quality=90)
def crop(src, box, dst, size=None):
    im = Image.open(src).convert('RGB').crop(box); im = im.resize(size) if size else im; im.save(dst, quality=92)
crop(f'{G}/A_day.jpg', (150, 600, 1250, 900), f'{G}/sign_A.jpg'); crop(f'{G}/D_day.jpg', (990, 640, 1600, 900), f'{G}/sign_D.jpg')
for k in ('marina', 'rossi', 'd0', 'd1', 'd2'):
    p = f'{F}/tex_hero_sign_{k}.png'
    if os.path.exists(p): Image.open(p).convert('RGB').save(f'{G}/sg_{k}.jpg', quality=92)

CSS = '''<style>body{margin:0;background:#16191d;font-family:Inter;color:#e9e6df}
.h{padding:46px 60px 10px}.h b{font-size:44px;letter-spacing:2px}.h span{display:block;font-size:19px;color:#a8a39a;margin-top:8px}
.tag{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}
img{display:block}.cap{font-size:20px;font-weight:800;margin:14px 0 4px}.sub{font-size:14.5px;color:#a8a39a;line-height:1.45}
.grid{display:grid;gap:26px;padding:0 60px}.card{background:#1e2227;padding:16px;border-radius:6px}
.pal{display:flex;gap:10px;margin-top:10px}.pal div{width:54px;height:54px;border-radius:4px}
.lbl{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}</style>'''


def sheet1():
    B = [('A', 'Corner apartment block', 'Red brick over a stone ground floor · stone cornice with dentils · iron balconies on corbels · rooftop water tank. Street level: Caffè Marina and Panificio Rossi with striped awnings and a blade sign.'),
         ('B', 'Art-deco office', 'Warm cream stone · full-height piers rising into a stepped crown with gold trim · recessed bronze spandrels · canopied bronze-and-glass entrance · gilded 3D lettering.'),
         ('C', 'Modern glass office', 'Blue-green curtain wall reflecting the street · aluminium mullions · projecting concrete floor bands · double-height lobby · NORDA in 3D letters · screened roof plant.'),
         ('D', 'Townhouse row', 'Three houses in terracotta, ochre and harbour-blue plaster · louvred green shutters folded open · clay-tile roofs with dormers and chimneys · barber, pharmacy, florist.')]
    cards = ''.join(f'<div class="card"><img src="{G}/{k}_day.jpg" style="width:100%"><div class="cap">{k} · {t}</div><div class="sub">{d}</div></div>' for k, t, d in B)
    els = ''.join(f'<div><img src="{G}/el_{k}.jpg" style="height:330px"><div class="lbl" style="text-align:center">PLAN {k}</div></div>' for k, _, _ in B)
    pal = ''.join(f'<div style="background:{c}"></div>' for c in ('#1f3d2f', '#6b2c1f', '#c9a45c', '#5a3b1c', '#3f6d7b', '#c8714f', '#d9ad55', '#9fb6c4', '#2f5d3a', '#1d2b4a'))
    return f'''<html><head>{CSS}</head><body style="width:3000px">
<div class="h"><i class="tag">CONCEPT 01</i><b>AURELIA ISLAND — CITY HERO BUILDINGS</b><span>Golden-hour key art and building studies · modelled in Blender from the approved elevations, lit and rendered in Cycles</span></div>
<div style="display:flex;gap:30px;padding:20px 60px">
  <img src="{G}/street_day.jpg" style="width:1960px;border-radius:4px">
  <div style="width:890px">
    <div class="lbl">MOOD</div><div class="sub" style="font-size:17px">A warm Mediterranean harbour city late in the afternoon: low sun raking across brick and stone, long shadows over the pavement, café tables out, awnings down. Each building has its own silhouette and colour so streets never repeat.</div>
    <div class="lbl" style="margin-top:26px">PALETTE</div><div class="pal">{pal}</div>
    <div class="lbl" style="margin-top:26px">ELEVATION PLANS</div><div style="display:flex;gap:8px;align-items:flex-end">{els}</div>
    <div class="lbl" style="margin-top:30px">DESIGN RULES</div><div class="sub" style="font-size:16px">• Every facade is real geometry: recessed windows, sills, cornices, balconies, piers and spandrels<br>• Signs are painted per shop with real fonts; large lettering is 3D<br>• Ground floors are always active: shops, cafés, lobbies with awnings and displays<br>• Three colour variants per design so no two neighbouring blocks match<br>• Same photo materials as the game, so renders match what you drive past</div>
  </div>
</div>
<div class="grid" style="grid-template-columns:repeat(4,1fr);margin-top:20px">{cards}</div>
<div style="height:50px"></div></body></html>'''


def sheet2():
    sg = ''.join(f'<div><img src="{G}/sg_{k}.jpg" style="width:330px;border-radius:3px"><div class="lbl" style="margin-top:8px">{n}</div></div>'
                 for k, n in (('marina', 'CAFFÈ MARINA · gold leaf serif'), ('rossi', 'PANIFICIO ROSSI · hand-painted'), ('d0', 'BARBIERE 1962 · navy & cream'), ('d1', 'FARMACIA · clean green sans'), ('d2', 'FIORI DI LUCIA · italic serif')) if os.path.exists(f'{G}/sg_{k}.jpg'))
    return f'''<html><head>{CSS}</head><body style="width:3000px">
<div class="h"><i class="tag">CONCEPT 02</i><b>AURELIA ISLAND — NIGHT & SIGNAGE</b><span>The same street after dark: random lit rooms, backlit shop signs, warm lamps over the pavement · sign graphics are painted per shop with real fonts</span></div>
<div style="display:flex;gap:30px;padding:20px 60px">
  <img src="{G}/street_night.jpg" style="width:1960px;border-radius:4px">
  <div style="width:890px;display:flex;flex-direction:column;gap:24px">
    <div><img src="{G}/A_night.jpg" style="width:890px;border-radius:4px"><div class="cap">A · Caffè Marina at night</div></div>
    <div><img src="{G}/D_night.jpg" style="width:890px;border-radius:4px"><div class="cap">D · Townhouses at night</div></div>
  </div>
</div>
<div style="padding:10px 60px"><div class="lbl">SHOPFRONT CLOSE-UPS</div><div style="display:flex;gap:30px"><img src="{G}/sign_A.jpg" style="height:420px;border-radius:4px"><img src="{G}/sign_D.jpg" style="height:420px;border-radius:4px"></div></div>
<div style="padding:20px 60px 60px"><div class="lbl">SIGN GRAPHICS (UNIQUE PER SHOP)</div><div style="display:flex;gap:26px;flex-wrap:wrap">{sg}</div></div>
</body></html>'''


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        for fn, out in ((sheet1, '/tmp/art/concept_01_hero_buildings.jpg'), (sheet2, '/tmp/art/concept_02_night_signage.jpg')):
            h = f'/tmp/art/{fn.__name__}.html'; open(h, 'w').write(fn())
            pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file://' + h); pg.wait_for_timeout(2500)
            pg.screenshot(path=out.replace('.jpg', '.png'), full_page=True, timeout=240000); pg.close()
            Image.open(out.replace('.jpg', '.png')).convert('RGB').save(out, quality=90); print('sheet', out)
        b.close()
