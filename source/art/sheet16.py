"""Concept 16 sheet: city blocks with depth. Tiles and hero from blender/sheet16_render.py, 'in the game now' from a Godot
TOUR picture. python3 sheet16.py <render dir> <game now> <out.jpg>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P, NOW, OUTF = sys.argv[1:4]; G = os.path.join(os.path.dirname(OUTF), 'g16'); os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json'))
items = [('office_glass', 'Glass office tower', 'The glass core', 'Fin-ribbed curtain wall with spandrel bands, a two-storey lobby, two setbacks, a lit crown over a plant screen'),
         ('office_stone', 'Stone office', 'Core edges, old town', 'Rusticated arcade base, punched windows in deep reveals, pilasters, a heavy cornice'),
         ('residential', 'Residential mid-rise', 'Streets round the core', 'Rendered walls with timber bands, balconies with glass rails, AC units and plants, a roof-terrace pergola'),
         ('mixed_tower', 'Mixed-use tower', 'Landmark plots', 'Five-storey podium with shopfront canopies, a slender banded tower, a stepped glass crown and mast')]
for k, *_ in items: grade.finish(f'{P}/{k}.png', f'{G}/{k}.jpg')
grade.finish(f'{P}/hero.png', f'{G}/hero.jpg')
im = Image.open(NOW).convert("RGB"); w, h = im.size; im.crop((0, 0, w, int(h * 0.62))).resize((900, int(900 * 0.62 * h / w))).save(f'{G}/now.jpg', quality=88)
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{st[k]["height"]:.0f} m · {st[k]["tris"] / 1000:.1f}k tris · merged per material like the HD city</div></div>' for k, t, reg, d in items)
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter,Arial;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}.card img{{width:100%;border-radius:3px}}
.cap{{font-size:20px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:15px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 16</i><b>AURELIA ISLAND — CITY BLOCKS WITH DEPTH</b><span>Four building types for the glass-tower core and the streets round it, replacing the flat window boxes: every facade has real relief · Blender, Cycles</span></div>
<div style="padding:10px 60px"><div class="lbl">ON THE STREET · CAR HEIGHT</div><img src="{G}/hero.jpg" style="width:2880px;border-radius:5px"></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">IN THE GAME NOW (APK 39)</div><img src="{G}/now.jpg" style="width:900px;border-radius:4px"></div>
 <div><div class="lbl">HOW IT GOES IN</div><div class="sub" style="font-size:16px;width:1600px;line-height:1.6">
 • Relief you can see from the car: window reveals, mullions and fins, spandrel bands, balconies, cornices; shadows and reflections break up every face<br>
 • Built from a small kit of parts and merged per material per city quarter, the same way as the HD city now, so the draw-call budget holds<br>
 • The plots, heights and street layout stay as approved; only the buildings standing on them change. Concept 10 shopfronts stay on the ground floors<br>
 • At night the lobbies, crowns and windows light up with the existing city lighting<br>
 • Far away the current low versions stay, so the skyline costs the same</div></div>
</div></body></html>'''
open(f'{G}/sheet16.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file://' + os.path.abspath(f'{G}/sheet16.html')); pg.wait_for_timeout(1500)
    pg.screenshot(path=f'{G}/sheet.png', full_page=True); b.close()
Image.open(f'{G}/sheet.png').convert('RGB').save(OUTF, quality=90)
print('sheet', OUTF)
