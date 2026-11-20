"""Concept 05 sheet: countryside, village and farms. Tiles from blender/sheet04_render.py in /tmp/s4final, current library strip from flora_preview.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s5final'; G = '/tmp/art/g5'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('farmhouse', 'Stone farmhouse', 'Farms, olive groves', 'Limestone, arched cart door, outside stair to the upper floor, vine pergola, terracotta roof'),
         ('village_row', 'Village row', 'Village main street', 'Three terraced houses in ochre, rose and blue lime-wash, iron balconies, flower boxes'),
         ('cottage', 'Lime-washed cottage', 'Village edge, coast', 'Single storey, blue shutters, painted skirting, pergola with a bench and pots'),
         ('barn_hq', 'Timber barn', 'Countryside farms', 'Red boards on a fieldstone base, sliding doors, hayloft hoist, ridge cupola, lean-to'),
         ('hay_shed', 'Hay shed', 'Farms', 'Open pole shed, rust-red roof, stacked square bales, round bales outside'),
         ('silos', 'Grain silos', 'Farm yards', 'Galvanised silos with caged ladders, catwalk and auger into a feed shed'),
         ('winery_hq', 'Wine cellar', 'Vineyards, hillside', 'Three stone arches, oak barrels racked inside, basket press, carved name board'),
         ('tractor', 'Tractor and trailer', 'Farm tracks, fields', 'Vintage red tractor with ribbed tyres and a tipping trailer of melons'),
         ('walls_fences', 'Walls and gates', 'Field boundaries, lanes', 'Dry-stone wall with coping, stone gate piers, five-bar gate, post-and-rail fence'),
         ('hay_field', 'Harvest', 'Fields after cutting', 'Round bales, some wrapped in white film, and a square-bale stack'),
         ('vineyard', 'Vineyard rows', 'Hills by the village', 'Chestnut posts and wires, twisted vine trunks, leafy canopy, grape bunches'),
         ('farm_stand', 'Farm stand', 'Country roads', 'Timber stall, green striped awning, crates of oranges, lemons, tomatoes, melons')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.18); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{st[k]["height"]:.0f} m · {tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur05/cur.jpg').resize((960, 480)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#e8d2a8', 'Limestone'), ('#f2eee4', 'Lime-wash'), ('#c4572e', 'Terracotta'), ('#3f6a4c', 'Shutter green'), ('#2f5a8c', 'Shutter blue'), ('#8e2416', 'Barn red')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 05</i><b>AURELIA ISLAND — COUNTRYSIDE, VILLAGE &amp; FARMS</b><span>Warm Adriatic farm country: limestone and lime-washed walls, terracotta roofs, painted shutters, timber barns, vines · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• One regional style for the whole countryside, so the village, farms and vineyards feel like the same place<br>• Real openings and depth everywhere: arched doorways, set-back doors, window reveals, stairs, balconies, pergolas<br>• Every farm gets a story: a barn, a hay shed or silos, a tractor in the yard, a wall or fence on the lane, bales or vines in the field<br>• Each piece gets a lighter far version and is placed as an instance, like the street furniture</div></div>
 <div><div class="lbl">REPLACES (CURRENT HOUSES AND BARNS)</div><img src="{G}/current.jpg" style="width:960px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet05.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet05.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_05.png', full_page=True); b.close()
Image.open('/tmp/art/concept_05.png').convert('RGB').save('/tmp/art/concept_05_countryside.jpg', quality=90)
