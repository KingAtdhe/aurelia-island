import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_tod','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')")
for side, tag in [(1, 'R'), (-1, 'L')]:
    r = pg.evaluate('''([side])=>{const g=__game,c=g.car,R=g.roads.find(r=>r.name==='Summit Pass');const p=g.roadPoint(R,61);p.h+=side*1.1;g.placeCar(p);const path=[];
      for(let s=0;s<200;s++){g.inp.gas=1;g.physics(1/60);if(s%20==0){const q=g.roadQuery(c.x,c.z,c.y,{});path.push([+(q.ok?q.d:99).toFixed(1),+c.y.toFixed(1),c.speed*3.6|0])}}g.inp.gas=0;return path}''', [side])
    print('WALL', tag, json.dumps(r)); time.sleep(6); shot('wall_' + tag)
