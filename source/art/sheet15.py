"""Concept 15 sheet: roadside trees for the Godot game. Tiles and hero from blender/sheet15_render.py (game weight, LOD 2),
'in the game now' crops from Godot TOUR pictures. python3 sheet15.py <render dir> <game now 1> <game now 2> <out.jpg>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P, NOW1, NOW2, OUTF = sys.argv[1:5]; G = os.path.join(os.path.dirname(OUTF), 'g15'); os.makedirs(G, exist_ok=True)
st = {}
for f in ('stats_plane.json', 'stats.json'):
    if os.path.exists(f'{P}/{f}'): st.update(json.load(open(f'{P}/{f}')))
st.setdefault('plane', {'tris': 5976, 'height': 16.0})
items = [('plane', 'London plane', 'City avenues', 'Clear mottled trunk, upswept limbs, a big broadleaf crown that lets light through'),
         ('oak', 'Field oak', 'Countryside, farm roads', 'Stout trunk, crooked spreading limbs, deep lobed-leaf dome'),
         ('stone_pine', 'Stone pine', 'Coast road, harbour', 'Tall bare curving trunk under a flat umbrella of needle tufts'),
         ('cypress', 'Italian cypress', 'Village, drives', 'A tight dark flame of upright sprays: the island’s skyline marker'),
         ('spruce', 'Norway spruce', 'Touge passes, mountains', 'Straight leader, whorls of drooping branches with upturned tips'),
         ('olive', 'Olive', 'Farms, hillsides', 'Twisted stems from one gnarled base, silver-grey open crown')]
for k, *_ in items: grade.finish(f'{P}/{k}.png', f'{G}/{k}.jpg')
grade.finish(f'{P}/hero.png', f'{G}/hero.jpg')
for i, src in enumerate((NOW1, NOW2)):
    im = Image.open(src).convert("RGB"); w, h = im.size; im.crop((0, int(h * 0.06), w, int(h * 0.7))).resize((640, int(640 * 0.64 * h / w))).save(f'{G}/now{i}.jpg', quality=88)
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{st[k]["height"]:.0f} m · near {st[k]["tris"] / 1000:.1f}k tris · far model + card beyond 200 m</div></div>' for k, t, reg, d in items)
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter,Arial;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}.card img{{width:100%;border-radius:3px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 15</i><b>AURELIA ISLAND — ROADSIDE TREES FOR THE GODOT GAME</b><span>The approved concept 04 trees brought to the phone game at game weight (what is drawn within 60 m of the car), replacing the low-poly Tripo trees · Blender, Cycles</span></div>
<div style="padding:10px 60px"><div class="lbl">ON THE ROAD · MIXED VERGE, CHASE-CAMERA HEIGHT</div><img src="{G}/hero.jpg" style="width:2880px;border-radius:5px"></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">IN THE GAME NOW (APK 39)</div><div style="display:flex;gap:16px"><img src="{G}/now0.jpg" style="width:640px;border-radius:4px"><img src="{G}/now1.jpg" style="width:640px;border-radius:4px"></div></div>
 <div><div class="lbl">HOW IT GOES IN</div><div class="sub" style="font-size:16px;width:1300px;line-height:1.6">
 • Real branching trunks and limbs with twig-spray foliage instead of faceted blobs: light comes through the crowns and the trunks read as wood<br>
 • Game weight near the car (numbers on each card), the lighter far model to 210 m, then the existing tree cards, so draw calls stay where they are now<br>
 • One foliage atlas and the bark set already in the game; the new leaf shader adds sun-through-leaves, shade inside the crown and a gentle sway<br>
 • Each region keeps its mix: planes in the city, oaks and olives inland, stone pines on the coast, cypresses in the village, spruce on the touge passes<br>
 • Tripo rocks, houses, barn and café stay as they are</div></div>
</div></body></html>'''
open(f'{G}/sheet15.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file://' + os.path.abspath(f'{G}/sheet15.html')); pg.wait_for_timeout(1500)
    pg.screenshot(path=f'{G}/sheet.png', full_page=True); b.close()
Image.open(f'{G}/sheet.png').convert('RGB').save(OUTF, quality=90)
print('sheet', OUTF)
