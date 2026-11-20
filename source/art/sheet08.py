"""Concept 08 sheet: roads and junctions. Tiles from blender/sheet08_render.py in /tmp/s8final, current roads strip from game/tests/roadcur.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s8final'; G = '/tmp/art/g8'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('road_highway', 'Highway', 'Coastal ring road', 'Two lanes each way, concrete median barrier, rumble strips, cat\'s eyes, marker posts'),
         ('road_country_road', 'Country road', 'Farm and valley roads', 'Worn asphalt with patches and sealed cracks, faded centre line, gravel shoulders'),
         ('road_hairpin', 'Mountain hairpin', 'Summit Pass, Serpentine', 'Switchback with a stone parapet, chevron boards and a cut rock bank'),
         ('road_city_crossing', 'City crossing', 'City grid', 'Zebra with beacons, dropped kerbs, tactile paving, green cycle lanes, gullies'),
         ('road_setts_street', 'Old-town lane', 'Old town', 'Granite setts with a central gutter, limestone pavements, heritage bollards'),
         ('road_roundabout', 'Roundabout', 'Mesa and Farm roundabouts', 'Planted island with a setts apron, chevrons, raised splitter islands'),
         ('road_junction', 'Signal junction', 'Avenues', 'Stop lines, lane arrows, ghost-island hatching, kerbed island with signals'),
         ('road_bridge_deck', 'Bridge deck', 'Beach Flyover, viaducts', 'Edge beams, steel parapet rails, expansion joint, deck drains, lamps'),
         ('road_roadworks', 'Road works', 'Random lane closures', 'Cone taper, yellow temporary lines, red-and-white barriers, trench, arrow board'),
         ('road_bus_layby', 'Bus lay-by', 'Avenues and towns', 'Tapered bay, raised boarding kerb, yellow markings, shelter'),
         ('road_car_park', 'Car park', 'Beach, stadium, town', 'Marked bays, accessible bay, wheel stops, pay station, lighting column, hedge'),
         ('road_gravel_track', 'Gravel track', 'Lake, Pine and Orchard trails', 'Wheel ruts with a grass crown, puddles, cattle grid with stone wings')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.12); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur08.jpg').resize((960, 320)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#3d3c3a', 'Asphalt'), ('#f0f0ea', 'Road white'), ('#e6a021', 'Road yellow'), ('#b8b5ad', 'Granite kerb'), ('#2f6b3a', 'Cycle green'), ('#1e4b8c', 'Chevron blue')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 08</i><b>AURELIA ISLAND — ROADS &amp; JUNCTIONS</b><span>Every road type gets its own surface, kerbs, markings and furniture, so you can tell where you are from the tarmac alone · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• Photo-scanned asphalt, granite setts and gravel; the road type sets the surface, not one grey everywhere<br>• Real kerbs with height, dropped kerbs at crossings, verges and shoulders instead of road meeting grass edge-on<br>• Markings follow one rulebook: white lanes and edges, yellow on the motorway median and for temporary works, blue chevrons on bends<br>• Junctions get stop lines, arrows and islands; roundabouts get planted centres and splitter islands<br>• Markings are decals on the road mesh, so they cost almost nothing to draw</div></div>
 <div><div class="lbl">REPLACES (CURRENT ROADS: RING, FARM ROAD, CITY, DESERT, SERPENTINE, TRAIL)</div><img src="{G}/current.jpg" style="width:960px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet08.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet08.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_08.png', full_page=True); b.close()
Image.open('/tmp/art/concept_08.png').convert('RGB').save('/tmp/art/concept_08_roads_junctions.jpg', quality=90)
