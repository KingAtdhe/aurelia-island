"""Concept 10 sheet: city street level. Tiles from blender/sheet08_render.py in /tmp/s10final, current roads strip from game/tests/look.py (base_city, base_old)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s10final'; G = '/tmp/art/g10'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('sh_cafe', 'Caffè Marina', 'Cafe', 'Striped awning on iron arms, terrace tables and chairs, menu board, planters, lit counter inside'),
         ('sh_boutique', 'LUNA', 'Boutique', 'Black steel frame, tall glazing, clothes rails and mannequins behind the glass, stone pilasters'),
         ('sh_pharmacy', 'Farmacia', 'Pharmacy', 'White frame, glowing green cross on a bracket, shelves of products inside'),
         ('sh_trattoria', 'Trattoria Sole', 'Restaurant', 'Oxblood timber front on a brick riser, red awning, dining room inside, tables out'),
         ('sh_bakery', 'Panetteria', 'Bakery', 'Painted timber shopfront, cream awning, A-board and planters'),
         ('sh_market', 'MERCATO', 'Grocer', 'Green front and awning over a stand of fruit and vegetable crates'),
         ('sh_gelateria', 'Gelateria Onda', 'Ice cream', 'Pastel pink front, striped awning, white bistro chairs'),
         ('sh_books', 'Libreria Faro', 'Bookshop', 'Navy timber front, hanging blade sign, shelves of books'),
         ('sh_pizzeria', 'Pizzeria Vesta', 'Pizzeria', 'Dark front with a wood-fired-oven room inside, terrace'),
         ('sh_shutter', 'Closed unit', 'Variety', 'Roller shutter in its box with posters, so not every bay is open'),
         ('sh_row', 'A street run', 'Old-town block', 'Four shops side by side under one building: how a block reads from the road'),
         ('sh_podium', 'Tower podium', 'Glass towers', 'Retail ground floor and a lit lobby portal with canopy and revolving door, replacing the black base')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.12); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur10.jpg').resize((1080, 250)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#173a34', 'Marina green'), ('#78221a', 'Oxblood'), ('#1a3a5c', 'Navy'), ('#e8d6b2', 'Cream'), ('#f2c9cf', 'Gelato pink'), ('#111113', 'Boutique black')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 10</i><b>AURELIA ISLAND — CITY STREET LEVEL</b><span>What you see at car height: real shopfronts with lit interiors, signs, awnings and terrace life instead of dark glass · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• Every city block gets a ground floor of shops: no more black bases or blank glass at street level<br>• Glass you can see through, onto a lit room: cafe counters, rails, shelves, dining rooms; brighter at night<br>• 16 original shop names in one Mediterranean family, each with its own colours and front<br>• Awnings, terrace tables, crates, A-boards and planters put life on the pavement, kept clear of the road<br>• Glass towers get a retail podium and a lit lobby portal; one bay in eight is a closed shutter for realism<br>• Instanced kit: a whole street costs little to draw</div></div>
 <div><div class="lbl">REPLACES (CURRENT CITY STREETS AT CAR HEIGHT)</div><img src="{G}/current.jpg" style="width:1080px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet10.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet10.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_10.png', full_page=True); b.close()
Image.open('/tmp/art/concept_10.png').convert('RGB').save('/tmp/art/concept_10_city_street_level.jpg', quality=90)
