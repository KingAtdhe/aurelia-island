import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
for x, z in [(76, -738), (522, -666), (921, 94)]:
    r = pg.evaluate('''([x,z])=>{const g=__game,c=g.obGrid.get(Math.floor(x/g.OG)+','+Math.floor(z/g.OG)),out=[];if(!c)return out;
      for(const o of c.o){if(Math.hypot(o[0]-x,o[1]-z)<Math.hypot(o[2],o[3])+4)out.push(['box',o.sp||'world',o.map(v=>+(+v).toFixed(1))])}
      for(const o of c.c){if(Math.hypot(o[0]-x,o[1]-z)<o[2]+4)out.push(['circ',o.sp||'world',o.map(v=>+(+v).toFixed(1))])}
      const q=g.roadQuery(x,z,100,{});return {out,road:q.ok?[q.road.name,+q.d.toFixed(1),q.road.hw]:null}}''', [x, z])
    print('BLK', x, z, json.dumps(r)[:900])
