"""Concept 13 sheet: ground, verges and grass. Tiles from blender/sheet13_render.py in /tmp/s13final; current-game strip from the live game."""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image, ImageEnhance
P = '/tmp/s13final'; G = '/tmp/art/g13'; os.makedirs(G, exist_ok=True)
items = [('meadow', 'Lush meadow', 'Countryside, coast', 'Photo-scanned turf under blade-by-blade grass with white, yellow and violet flowers; dense by the road, thinning with distance'),
         ('dry', 'Dry summer grass', 'Coast, south slopes', 'Straw-coloured grass over sun-dried turf, a short layer underneath, scattered stones'),
         ('verge', 'Road verge', 'Every rural road', 'Edge line, gravel shoulder with weeds and grit, grass strip rising to the field, posts with red reflectors'),
         ('forest', 'Forest floor', 'Forest trails', 'Needle and leaf litter with moss in the hollows, ferns, a fallen branch, cones, a mossy boulder'),
         ('track', 'Dirt track', 'Farm and forest tracks', 'Two wheel ruts in stony dirt with loose stones, grass crown in the middle, grass banks'),
         ('dune', 'Dune edge', 'Beaches, coastal highway', 'Rippled sand with marram-grass tufts and shell grit'),
         ('outcrop', 'Granite outcrop', 'Mountains, meadows', 'Light granite with fracture faces and moss on the tops, sunk into the turf: no more black lumps')]
for k, *_ in items + [('hero',)]:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); CROP = {'hero': (0, 150, 1680, 720), 'verge': (0, 56, 840, 560), 'track': (0, 50, 840, 560)}
    if k in CROP: im_ = im_.crop(CROP[k])
    im_ = ImageEnhance.Brightness(im_).enhance(1.04); im_ = ImageEnhance.Color(im_).enhance(1.08); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
# current game strip (same spots, phone Medium)
cur = [Image.open(f'/home/claude/live/a4_{i}.png').convert('RGB').resize((844, 390)) for i in (1, 2)]
strip = Image.new('RGB', (844, 780)); [strip.paste(c, (0, i * 390)) for i, c in enumerate(cur)]; strip.save(f'{G}/current.jpg', quality=85)
# texture swatches: crops of the photo sets used
import numpy as np
sw = [('Grass001', 'Meadow turf'), ('Grass003', 'Dry turf'), ('Gravel022', 'Verge gravel'), ('Ground042', 'Forest litter'), ('Moss002', 'Moss'), ('Ground067', 'Stony dirt'), ('Ground080', 'Rippled sand'), ('Rock048', 'Granite')]
for n, _ in sw: Image.fromarray(np.fromfile(f'/home/claude/photo13/{n}_Color.raw', np.uint8).reshape(512, 512, 4)[:256, :256, :3]).resize((120, 120)).save(f'{G}/sw_{n}.jpg', quality=90)
pal = ''.join(f'<div><img src="{G}/sw_{n}.jpg" style="width:92px;height:92px;border-radius:4px;display:block"><div class="sub" style="font-size:12px;margin-top:6px;width:96px">{t}</div></div>' for n, t in sw)
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div></div>' for k, t, reg, d in items)
cards += f'<div class="card"><img src="{G}/current.jpg" style="width:100%;border-radius:3px;opacity:.92"><div class="cap">Replaces<span class="reg">Current game</span></div><div class="sub">Flat single-tone ground, no grass near the road, dark lumps for rocks (coast road and forest trail today, phone Medium)</div></div>'
html = f'''<html><head><meta charset="utf-8"><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;padding:10px 60px 20px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}.rules{{font-size:16px;color:#a8a39a;line-height:1.6}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 13</i><b>AURELIA ISLAND — GROUND, VERGES &amp; GRASS</b><span>Photo-scanned ground under real grass, verges that look built, rocks that read as stone · modelled in Blender, rendered in Cycles at chase-camera height · for approval before building into the map</span></div>
<div style="display:flex;gap:22px;padding:20px 60px 10px">
 <div class="card" style="flex:0 0 1900px"><img src="{G}/hero.jpg" style="width:100%;border-radius:3px"><div class="cap">Coastal road at chase-camera height<span class="reg">The look we are building toward</span></div><div class="sub">Gravel shoulder, edge line and dry summer grass with granite boulders; the grass thins into the ground texture with distance, as it will in the game</div></div>
 <div style="flex:1"><div class="lbl">HOW IT GOES INTO THE GAME</div><div class="rules">
 • Every ground type becomes one photo-scanned PBR set (colour, normal, roughness) plus a fine detail layer, blended by the existing splat maps. No flat colour anywhere.<br><br>
 • Grass near the road becomes instanced clumps baked from these blade models (cards with alpha, wind sway), drawn within 35 m of the camera on phones and 55 m on High, fading out; beyond that the turf texture carries the look.<br><br>
 • Verges are built along every road: gravel shoulder strip, weeds, edge posts. Tracks get real ruts and a grass crown.<br><br>
 • Rocks are re-sculpted in light granite with baked ambient occlusion and moss on the tops, so they read as stone in shade.<br><br>
 • Phone budget (Medium): about +40 draw calls and up to 150k extra triangles near the camera. If a phone slows down, the grass range drops first.</div>
 <div class="lbl" style="margin-top:26px">MATERIALS (CC0, PHOTO-SCANNED)</div><div style="display:flex;gap:12px;flex-wrap:wrap">{pal}</div></div>
</div>
<div class="grid">{cards}</div>
<div style="height:40px"></div></body></html>'''
open('/tmp/art/sheet13.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet13.html'); pg.wait_for_timeout(2500)
    pg.screenshot(path='/tmp/art/concept_13.png', full_page=True); b.close()
Image.open('/tmp/art/concept_13.png').convert('RGB').save('/tmp/art/concept_13_ground_verges_grass.jpg', quality=90)
print('ok', Image.open('/tmp/art/concept_13.png').size)
