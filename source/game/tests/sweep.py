import json, os
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_cam','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(15)
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
roads = pg.evaluate("__game.roads.map(r=>[r.name,r.n,r.type])"); print('ROADS', json.dumps(roads))
spots = []; names = set()
for nm, n, ty in sorted(roads, key=lambda r: -r[1]):
    if nm in names or n < 30: continue
    names.add(nm); spots.append((nm, int(n * 0.35))); 
    if len(spots) >= 20: break
log = []
for k, (nm, i) in enumerate(spots):
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i))}''', [nm, i]); time.sleep(5)
    pg.evaluate("__game.inp.gas=1"); time.sleep(4); pg.evaluate("__game.inp.gas=0")
    st = pg.evaluate("(()=>{const c=__game.car,g=__game.ground(c.x,c.z,c.y+1);return {spd:c.speed*3.6|0,y:+c.y.toFixed(2),gy:+g.y.toFixed(2),surf:g.surf,air:c.air,frozen:c.frozen}})()")
    shot('sw_%02d' % k); log.append((k, nm, st)); print('SPOT', k, nm, json.dumps(st))
