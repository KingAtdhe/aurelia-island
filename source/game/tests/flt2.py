import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_tod','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')")
r = pg.evaluate('''()=>{const g=__game,D=g.FLO.data,out=[];for(const sp of ['spruce','pine','spruce_b']){const a=D.instances[sp];for(let i=0;i<a.length;i+=8){const G=g.ground(a[i],a[i+2],a[i+1]+2);const d=a[i+1]-G.y;if(d>6&&out.length<6)out.push([sp,a[i]|0,a[i+1]|0,a[i+2]|0,+d.toFixed(1)])}}return out}''')
print('TREES', json.dumps(r))
x, y, z = r[0][1], r[0][2], r[0][3]
q = pg.evaluate("([x,z])=>{const g=__game;let best=null,bd=1e9;for(const R of g.roads)for(let i=0;i<R.n;i++){const d=Math.hypot(R.p[i*3]-x,R.p[i*3+2]-z);if(d<bd){bd=d;best=[R.name,i]}}return [best,bd|0]}", [x, z]); print('NEAREST', q)
pg.evaluate("([n,i])=>{const g=__game,R=g.roads.find(r=>r.name===n);g.placeCar(g.roadPoint(R,Math.max(0,i-8)))}", q[0]); time.sleep(8); shot('flt_a')
pg.evaluate("([n,i])=>{const g=__game,R=g.roads.find(r=>r.name===n);g.placeCar(g.roadPoint(R,Math.min(R.n-1,i+3)))}", q[0]); time.sleep(8); shot('flt_b')
