"""Concept 06 sheet: harbour and coast. Tiles from blender/sheet04_render.py in /tmp/s4final, current library strip from flora_preview.py."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade
from PIL import Image
P = '/tmp/s6final'; G = '/tmp/art/g6'; os.makedirs(G, exist_ok=True)
st = json.load(open(f'{P}/stats.json')); lod = {}
items = [('boats', 'Fishing boats', 'Fishing village, harbour', 'Painted timber hulls with a contrast strake, wheelhouse, mast and derrick, nets, fish boxes, tyre fenders'),
         ('sail_yacht', 'Sailing yacht', 'Marina', '12 m sloop: boot stripe, teak deck, coachroof ports, twin wheels, rigged mast, sail cover'),
         ('motor_yacht', 'Motor yacht', 'Marina', '15 m flybridge cruiser: dark glazing bands, bimini, swim platform, chrome rails'),
         ('rowing_boat', 'Rowing boat', 'Beaches', 'Clinker dinghy pulled up on the sand, oars on the thwarts, anchor line'),
         ('jetty', 'Timber jetty', 'Marina, fishing village', 'Plank deck on driven piles, cleats, ladder, lamp post with a lifebuoy'),
         ('quay_hq', 'Harbour quay', 'Harbour front', 'Dressed stone coping, cast-iron bollards and ropes, fenders, chain, crates and nets'),
         ('beach_set', 'Beach set', 'Beaches', 'Striped umbrellas, teak loungers with towels, cool box, beach bag and ball'),
         ('lifeguard', 'Lifeguard tower', 'Main beach', 'Raised hut on splayed legs, ramp, flag, rescue board and ring'),
         ('beach_bar', 'Beach bar', 'Beach, promenade end', 'Reed-thatched roof, bamboo counter, stools, bottle shelves, string lights'),
         ('breakwater', 'Breakwater and buoys', 'Harbour mouth', 'Concrete tetrapods, green harbour beacon, red can buoy, yellow mooring buoy'),
         ('promenade', 'Seafront promenade', 'Harbour town', 'Stone sea wall, white iron railing, double globe lamps, bench, clipped bay tree'),
         ('harbour_kiosk', 'Harbour kiosk', 'Ferry quay, marina', 'Ticket and ice-cream kiosk with a striped awning, poster, ice-cream cart')]
from PIL import ImageEnhance
for k, *_ in items:
    im_ = Image.open(f'{P}/{k}.png').convert('RGB'); im_ = ImageEnhance.Brightness(im_).enhance(1.0 if k in ('boats', 'sail_yacht', 'motor_yacht', 'jetty', 'quay_hq', 'breakwater') else 1.18); im_ = ImageEnhance.Color(im_).enhance(1.1); im_.save(f'{G}/{k}_b.png')
    grade.finish(f'{G}/{k}_b.png', f'{G}/{k}.jpg')
def tri(k):
    t = st[k]['tris']; l = lod.get(k)
    return f'{t / 1000:.1f}k tris' + (f' · far {l / 1000:.1f}k' if l else '')
cards = ''.join(f'<div class="card"><img src="{G}/{k}.jpg" style="width:100%;border-radius:3px"><div class="cap">{t}<span class="reg">{reg}</span></div><div class="sub">{d}</div><div class="num">{st[k]["height"]:.0f} m · {tri(k)}</div></div>' for k, t, reg, d in items)
Image.open('/tmp/cur06.jpg').resize((960, 480)).save(f'{G}/current.jpg', quality=85)
pal = ''.join(f'<div><div style="width:62px;height:62px;border-radius:4px;background:{c}"></div><div class="sub" style="font-size:12px;margin-top:6px">{n}</div></div>' for c, n in (('#0f2e5c', 'Harbour blue'), ('#a3261a', 'Boat red'), ('#f0eee8', 'Hull white'), ('#b98a52', 'Teak'), ('#e6d2b0', 'Limestone'), ('#d99a22', 'Buoy yellow')))
html = f'''<html><head><style>body{{margin:0;background:#16191d;font-family:Inter;color:#e9e6df;width:3000px}}
.h{{padding:46px 60px 10px}}.h b{{font-size:44px;letter-spacing:2px}}.h span{{display:block;font-size:19px;color:#a8a39a;margin-top:8px}}
.tag{{font-style:normal;display:inline-block;vertical-align:middle;background:#c9a45c;color:#16191d;font-weight:800;font-size:14px;padding:5px 10px;letter-spacing:2px;margin-right:12px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:22px;padding:20px 60px}}.card{{background:#1e2227;padding:14px;border-radius:6px}}
.cap{{font-size:19px;font-weight:800;margin:12px 0 4px}}.reg{{font-weight:600;font-size:13px;color:#c9a45c;margin-left:10px;letter-spacing:1px}}.sub{{font-size:14px;color:#a8a39a;line-height:1.45}}
.num{{font-size:12px;color:#7d786f;margin-top:6px;letter-spacing:1px}}.lbl{{font-size:12px;color:#8d887f;letter-spacing:3px;font-weight:700;margin:6px 0 10px}}</style></head><body>
<div class="h"><i class="tag">CONCEPT 06</i><b>AURELIA ISLAND — HARBOUR &amp; COAST</b><span>A working Adriatic waterfront: painted timber boats, white yachts, timber jetties, stone quays, striped umbrellas · modelled in Blender, rendered in Cycles</span></div>
<div class="grid">{cards}</div>
<div style="display:flex;gap:60px;padding:10px 60px 60px">
 <div><div class="lbl">PALETTE</div><div style="display:flex;gap:14px">{pal}</div>
  <div class="lbl" style="margin-top:26px">DESIGN RULES</div><div class="sub" style="font-size:16px;width:720px">• Boats are real hulls (lofted sections, strakes, decks), not boxes and spheres, and sit at a true waterline<br>• The harbour reads as working (crates, nets, ropes, fenders) and the beaches as holiday (umbrellas, bar, lifeguard)<br>• Painted colours repeat across the coast: harbour blue, boat red, hull white, teak and limestone<br>• Each piece gets a lighter far version and is placed as an instance; the big cruise and cargo ships come in a later pass</div></div>
 <div><div class="lbl">REPLACES (CURRENT HARBOUR AND BEACHES)</div><img src="{G}/current.jpg" style="width:960px;border-radius:4px;opacity:.9"></div>
</div></body></html>'''
open('/tmp/art/sheet06.html', 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 3000, 'height': 1000}); pg.goto('file:///tmp/art/sheet06.html'); pg.wait_for_timeout(2000)
    pg.screenshot(path='/tmp/art/concept_06.png', full_page=True); b.close()
Image.open('/tmp/art/concept_06.png').convert('RGB').save('/tmp/art/concept_06_harbour_coast.jpg', quality=90)
