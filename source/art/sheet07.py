"""Concept 07 sheet: mountains, desert and roadside. Tiles from blender/sheet04_render.py in /tmp/s4final, current library strip from flora_preview.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s7final'; G = '/tmp/art/g7'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('boulders', 'Granite boulders', 'Mountains, forest', 'Fractured faces, weathered edges, a scatter of loose stones; three sizes'),
         ('cliff', 'Granite cliff', 'Mountain road cuts', 'Displaced rock wall with vertical jointing, ledges, ragged top and a talus foot'),
         ('scree', 'Scree fan', 'Below gullies', 'Hundreds of angular stones, big at the toe, gravel at the top'),
         ('hoodoo', 'Sandstone hoodoo', 'Desert', 'Banded pillar with a hard cap rock, eroded blocks around it'),
         ('cliff_sand', 'Sandstone cliff', 'Desert canyons', 'Red layered wall with bedding ledges and fallen blocks'),
         ('windpump', 'Desert windpump', 'Desert ranch tracks', 'Lattice tower, 18-blade wheel and vane, water tank on stilts, stone trough'),
         ('guardrail_hq', 'W-beam guardrail', 'All rural roads', 'Corrugated steel beam on posts with blockouts, reflectors and a flared end'),
         ('parapet', 'Stone parapet', 'Mountain roads, passes', 'Dressed stone wall with coping and drains, kilometre stone, snow poles'),
         ('tunnel_portal', 'Tunnel portal', 'Mountain tunnels', 'Voussoir arch with a keystone, ashlar headwall, cornice, plaque, lamps, wing walls'),
         ('catch_fence', 'Rockfall fence', 'Under cliffs', 'Steel posts with back-stays and ring net, with caught rocks'),
         ('desert_stop', 'Desert roadside stop', 'Desert highway', 'Weathered billboard, oil drums, tyre stack, broken fence'),
         ('lookout', 'Mountain lookout', 'Viewpoints and lay-bys', 'Stone-walled terrace, timber shelter, coin binoculars, orientation table, bench')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.12); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{st[k]["height"]:.0f} m · {tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur07.jpg').resize((960, 480)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#8a8274', 'Granite'), ('#c9743f', 'Sandstone'), ('#d9cdb6', 'Dressed stone'), ('#a6aaad', 'Galvanised steel'), ('#a3261a', 'Signal red'), ('#d99a22', 'Snow-pole yellow')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 07</i><b>AURELIA ISLAND — MOUNTAINS, DESERT &amp; ROADSIDE</b><span>Sculpted granite and sandstone, real cliff faces for road cuts, and the hardware that lines the roads · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• Rocks are sculpted geometry (fracture planes, jointing, bedding) with one photo-scanned rock texture, tinted grey in the mountains and red in the desert<br>• Road cuts get real cliff faces and talus instead of smooth terrain, with rockfall fences under the steepest ones<br>• One roadside family across the island: W-beam guardrail on fast roads, stone parapets and snow poles on the passes, stone portals on every tunnel<br>• Each piece gets a lighter far version and is placed as an instance</div></div>
 <div><div class="lbl">REPLACES (CURRENT MOUNTAIN AND DESERT ROADS)</div><img src="{G}/current.jpg" style="width:960px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet07.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet07.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_07.png', full_page=True); b.close()
Image.open('/tmp/art/concept_07.png').convert('RGB').save('/tmp/art/concept_07_mountains_desert_roadside.jpg', quality=90)
