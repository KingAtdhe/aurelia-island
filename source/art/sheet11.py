"""Concept 11 sheet: touge kit. Tiles from blender/sheet08_render.py in /tmp/s11final, current roads strip from game/tests/look.py (vx_mtn) + drive.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s11final'; G = '/tmp/art/g11'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('tg_hairpin', 'Touge hairpin', 'Summit Pass, Serpentine', 'Tight switchback cut into the hill: lattice slope, spillway, guard pipe and chevrons round the outside, mirror and light at the apex'),
         ('tg_straight', 'Pass road', 'All mountain roads', 'Yellow no-overtaking line, retaining wall and U-ditch uphill, guard pipe on the drop, conifers below'),
         ('tg_lattice', 'Lattice slope', 'Cut slopes', 'Cast concrete frame holding a steep cut, grass growing in every cell, crown beam on top'),
         ('tg_shotcrete', 'Shotcrete cut', 'Rock cuttings', 'Sprayed concrete face with rows of weep pipes, rust streaks and a drainage berm'),
         ('tg_wall', 'Retaining wall', 'Uphill edge', 'Battered concrete wall with formwork lines, weep holes, coping and a steel handrail'),
         ('tg_ditch', 'U-ditch', 'Uphill edge', 'Precast concrete gutter with joints, a wet dark bottom and cast-iron grates'),
         ('tg_mirror', 'Curve mirror', 'Blind bends', 'Orange pole with twin convex mirrors angled round the bend, hood and plate'),
         ('tg_guardpipe', 'Guard pipe', 'Drop side', 'White round posts with three steel pipes and amber reflectors, the touge classic'),
         ('tg_cedars', 'Conifer wall', 'Both sides', 'Tall straight conifers planted close, so the road runs through a dark green corridor'),
         ('tg_light', 'Hairpin light', 'Every hairpin', 'Tapered pole and curved arm with a warm sodium lantern'),
         ('tg_spillway', 'Stepped spillway', 'Cut slopes', 'Concrete steps carrying rain off the slope into the gutter'),
         ('tg_posts', 'Posts and poles', 'Roadside', 'Kilometre post, striped snow poles with arrows, reflector posts')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.12); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur11.jpg').resize((1080, 250)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#b8b6ae', 'Cast concrete'), ('#e6a021', 'Centre yellow'), ('#f0f0ea', 'Guard white'), ('#f26b10', 'Mirror orange'), ('#1b3a1c', 'Conifer green'), ('#ff9a40', 'Sodium light')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 11</i><b>AURELIA ISLAND — TOUGE (MOUNTAIN PASS) KIT</b><span>The mountain roads rebuilt the way CarX touge maps feel: cut slopes, concrete, guard pipes, mirrors and a wall of trees right at the road · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• The road is enclosed: cut slope and wall on the uphill side, guard pipe and trees on the drop side, never open grass<br>• Cut slopes alternate between lattice frames and shotcrete, with spillways and weep pipes so they read as engineered<br>• Every hairpin gets the full set: chevrons, curve mirror, sodium light, rubber on the apex<br>• Yellow double centre line on the passes; white edge lines; U-ditch with grates along the uphill edge<br>• Conifers planted close and dense along the passes (instanced, with far cards)<br>• Pieces follow the road mesh, so every pass gets them without hand placing</div></div>
 <div><div class="lbl">REPLACES (CURRENT MOUNTAIN ROADS)</div><img src="{G}/current.jpg" style="width:1080px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet11.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet11.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_11.png', full_page=True); b.close()
Image.open('/tmp/art/concept_11.png').convert('RGB').save('/tmp/art/concept_11_touge.jpg', quality=90)
