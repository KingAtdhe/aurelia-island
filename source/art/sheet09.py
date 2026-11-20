"""Concept 09 sheet: landmarks. Tiles from blender/sheet08_render.py in /tmp/s9final, current roads strip from game/tests/lmcur.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s9final'; G = '/tmp/art/g9'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('lm_church_hq', 'Village church', 'Valley village', 'Romanesque nave in warm limestone, terracotta roofs, apse, campanile with belfry, bell and clock; churchyard with cypresses'),
         ('lm_church_detail', 'West front', 'Church detail', 'Rose window with tracery, columned round-arched portal up three steps, stone string course and cross'),
         ('lm_lighthouse_hq', 'Lighthouse', 'Lighthouse Point', 'Tapered white tower with a red band on a granite base, keeper\'s cottage, oil store and walled yard'),
         ('lm_lighthouse_detail', 'Lantern', 'Lighthouse detail', 'Corbelled gallery and railing, diagonal-glazed lantern, glowing Fresnel lens, red dome, ventilator and vane'),
         ('lm_windmill_full', 'Windmill', 'Farmland ridge', 'Whitewashed tower mill, conical tiled cap, tail pole and cart wheel; the sails turn in the game'),
         ('lm_windmill_detail', 'Sails and cap', 'Windmill detail', 'Lattice sails, two set with canvas and two furled, bowsprit with stays to every tip'),
         ('lm_fuel_station_hq', 'Fuel station', 'Farm Road', 'Lit AURELIA canopy over two pump islands, glazed shop with cafe, car-wash bay, price totem'),
         ('lm_fuel_detail', 'Forecourt', 'Fuel station detail', 'Modern dispensers with screens, nozzles and hoses, crash posts, LED downlights, ice chest, planters'),
         ('lm_stadium_hq', 'Stadium', 'East of the city', 'White fin facade over a glazed concourse, membrane roof on trusses, floodlight masts, named entrance'),
         ('lm_stadium_detail', 'Inside the bowl', 'Stadium detail', 'Two seating tiers in club colours, hospitality boxes, vomitories, scoreboards, striped pitch with full markings')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.12); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur09.jpg').resize((1080, 333)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#e3c9a0', 'Limestone'), ('#c4683c', 'Terracotta'), ('#f2f0ea', 'Whitewash'), ('#b8231a', 'Lighthouse red'), ('#155c42', 'Aurelia green'), ('#1f4f9e', 'Club blue')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 09</i><b>AURELIA ISLAND — LANDMARKS</b><span>Five places you navigate by, rebuilt as hero models: the church, the lighthouse, the windmill, the fuel station and the stadium · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• One Mediterranean family: warm limestone, whitewash and terracotta, with green and club colours only where they belong<br>• Silhouettes readable from a kilometre away: campanile, red-banded tower, sails, lit canopy, white stadium ring<br>• Close-up detail where you stop: portals, lanterns, sails, pumps and the inside of the bowl<br>• Each landmark keeps its current spot and footprint, so roads and collisions stay as they are<br>• All names and branding are original to Aurelia Island</div></div>
 <div><div class="lbl">REPLACES (CURRENT CHURCH, LIGHTHOUSE, WINDMILL, FUEL STATION, STADIUM)</div><img src="{G}/current.jpg" style="width:1080px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet09.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet09.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_09.png', full_page=True); b.close()
Image.open('/tmp/art/concept_09.png').convert('RGB').save('/tmp/art/concept_09_landmarks.jpg', quality=90)
