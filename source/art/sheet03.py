import sys; sys.path.insert(0, '/tmp/art')
import grade
from PIL import Image
P = '/tmp/props'; G = '/tmp/art/g3'; import os; os.makedirs(G, exist_ok=True)
items = [('lamp_city', 'Double lantern street lamp', 'Fluted column on a moulded base, scroll arms, three hexagonal glass lanterns, brass collars · 5.6 m'),
         ('bin', 'Litter bin', 'Slatted cast-iron drum, brass bands, domed lid with a flap · 1.1 m'),
         ('bollard', 'Bollard', 'Tapered cast iron with a brass ring · 1.0 m'),
         ('bench', 'Park bench', 'Scrolled cast-iron ends, oiled hardwood slats · 1.9 m'),
         ('shelter', 'Bus shelter', 'Green steel frame, curved glass roof, lit advert panel, route post · 4.2 m'),
         ('kiosk', 'News kiosk', 'Octagonal, magazines behind glass, domed roof with finial, name band · 4.0 m'),
         ('mailbox', 'Post box', 'Saffron pillar box with brass finial and letter slot · 1.6 m'),
         ('planter', 'Stone urn planter', 'Carved stone urn, clipped boxwood, flowers · 1.4 m'),
         ('cafe', 'Café set', 'Marble bistro table, rattan chairs, umbrella with green valance'),
         ('scooter', 'Retro scooter', 'Step-through, leg shield, saddle, round headlamp (paint varies)'),
         ('phonebooth', 'City map totem', 'Lit street map both sides, brass crest band · 2.4 m'),
         ('fountain', 'Drinking fountain', 'Cast-iron column, brass spout, stone basin · 1.6 m')]
for k, _, _ in items: grade.finish(f'{P}/hq_{k}.png', f'{G}/{k}.jpg')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}</div><div class="sub">{d}</div></div>' for k, t, d in items)
pal = ''.join(f'<div><div style="width:70px;height:70px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#0f2a1f', 'Marina green'), ('#c79a4a', 'Brass'), ('#e1d9c8', 'Limestone'), ('#7a5236', 'Hardwood'), ('#d6851a', 'Saffron'), ('#1a1a1c', 'Iron')))
before = ''.join(f'<img src="{P}/current_{k}.png" style="width:150px;border-radius:3px;opacity:.85">' for k in ('lamp', 'bin', 'bollard', 'bench', 'shelter', 'kiosk', 'mailbox', 'planter', 'cafe', 'scooter', 'phonebooth'))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 03</i><b>AURELIA ISLAND — STREET FURNITURE</b><span>One family for the old town: cast iron in deep Marina green with brass collars, limestone and oiled hardwood · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:80px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:16px">{pal}</div></div>
 <div style="width:900px"><div class="lbl">DESIGN RULES</div><div class="sub" style="font-size:16px">• Every piece shares the same green, brass and stone so streets feel designed, not assembled<br>• Silhouettes are readable at driving speed: lanterns, domes and finials catch the eye<br>• Detail is real geometry (flutes, scrolls, slats, valances), with cheap far versions for distance<br>• Modern areas (glass offices, highway) keep the existing grey steel kit</div></div>
 <div><div class="lbl">REPLACES (CURRENT)</div><div style="display:flex;gap:8px">{before}</div></div>
</div></body></html>'''
open('/tmp/art/sheet03.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet03.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_03.png', full_page=True); b.close()
Image.open('/tmp/art/concept_03.png').convert('RGB').save('/tmp/art/concept_03_street_furniture.jpg', quality=90)
im = Image.open('/tmp/art/concept_03_street_furniture.jpg'); im.resize((1500, int(im.size[1] / 2))).save('/tmp/art/c3prev.jpg', quality=80)
