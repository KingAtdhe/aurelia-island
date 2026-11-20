"""Concept 04 sheet: trees and vegetation. Tiles from blender/sheet04_render.py in /tmp/s4final, current library strip from flora_preview.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s4final'; G = '/tmp/art/g4'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = json.load(open(f'{P}/lod.json'))
items = [('plane', 'London plane', 'City avenues and squares', 'Clear trunk with flaking camouflage bark, upswept limbs, broad maple-like leaves'),
         ('oak', 'Field oak', 'Countryside, farms', 'Stout trunk, crooked spreading limbs, lobed leaves, broad dome'),
         ('birch', 'Silver birch', 'Forest edges, parks', 'White bark with dark lenticels, light crown, hanging twigs'),
         ('olive', 'Olive', 'Farms, village, hillsides', 'Three twisted stems from one gnarled base, silver-grey leaves'),
         ('stone_pine', 'Stone pine', 'Coast, harbour parks', 'Tall bare curving trunk, flat umbrella canopy of needle tufts'),
         ('cypress', 'Italian cypress', 'Village, drives, chapel', 'Tight flame-shaped column of upright scale-leaf sprays'),
         ('date_palm', 'Date palm', 'Marina, beach promenade', 'Leaf-base scarred trunk, 40 arching feather fronds, dead-frond skirt, dates'),
         ('spruce', 'Norway spruce', 'Mountains, national park', 'Straight leader, whorls of drooping branches with upturned tips'),
         ('shrubs', 'Garden shrubs', 'Gardens, roundabouts, hedgerows', 'Flowering oleander, clipped boxwood hedge, bay laurel'),
         ('understory', 'Forest floor', 'Forest trails', 'Fern clumps and a fallen log'),
         ('meadow', 'Meadow', 'Verges, fields, countryside', 'Grass tufts with poppies, daisies, cornflowers and buttercups'),
         ('desert', 'Desert planting', 'Desert, canyon roads', 'Blue agave rosettes and flowering prickly pear (modelled, no cards)')]
for k, *_ in items: grade.finish(f'{P}/{k}.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{st[k]["height"]:.0f} m · {tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/atlas_prev.jpg').resize((300, 300)).save(f'{G}/atlas.jpg', quality=88)
cur = Image.open('/tmp/flora/flora_beauty.jpg'); w, h = cur.size; cur.crop((0, int(h * 0.2), int(w * 0.85), int(h * 0.75))).resize((900, int(900 * 0.55 * h / (0.85 * w)))).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#2f4a1f', 'Summer green'), ('#5d6b4a', 'Olive silver'), ('#22382a', 'Conifer'), ('#7a8a3a', 'Dry grass'), ('#c9b48a', 'Plane bark'), ('#e6e2d8', 'Birch')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 04</i><b>AURELIA ISLAND — TREES &amp; VEGETATION</b><span>Twelve plant sets, one per landscape role: real branching trunks and limbs dressed with painted twig sprays · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">FOLIAGE ATLAS · 16 CELLS</div><img src="{G}/atlas.jpg" style="width:300px;border-radius:4px"></div>
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• Every tree is built from branching geometry (trunk, limbs, twigs), dressed with painted twig sprays rather than flat painted shapes<br>• One 2048 px foliage atlas and five bark textures serve the whole island, so draw calls stay low<br>• Each region gets its own mix so it reads at a glance: planes in the city, olives and cypresses in the village, stone pines and palms on the coast, spruce in the mountains<br>• Every species has a lighter far version for distance (numbers on each card), with flat cut-out cards beyond that, like today</div></div>
 <div><div class="lbl">REPLACES (CURRENT LIBRARY)</div><img src="{G}/current.jpg" style="width:900px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet04.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet04.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_04.png', full_page=True); b.close()
Image.open('/tmp/art/concept_04.png').convert('RGB').save('/tmp/art/concept_04_trees_vegetation.jpg', quality=90)
