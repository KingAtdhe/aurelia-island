import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
r = pg.evaluate('''()=>{const g=__game,R=g.roads.find(r=>r.name==='Pit Access');const pts=[];for(let i=0;i<R.n;i++)pts.push([R.p[i*3]|0,R.p[i*3+2]|0]);
 const c=g.obGrid.get(Math.floor(922/120)+','+Math.floor(94/120));const near=c?c.o.filter(o=>Math.hypot(o[0]-922,o[1]-94)<25).map(o=>o.map(v=>+v.toFixed(1))):[];const nc=c?c.c.filter(o=>Math.hypot(o[0]-922,o[1]-94)<25).map(o=>o.map(v=>+v.toFixed(1))):[];
 return {n:R.n,hw:R.hw,closed:R.closed,pts:pts.filter((p,i)=>i%2==0),near,nc}}''')
print('PIT', json.dumps(r))
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
pg.evaluate('''()=>{const g=__game,R=g.roads.find(r=>r.name==='Pit Access');let bi=0,bd=1e9;for(let i=0;i<R.n;i++){const d=Math.hypot(R.p[i*3]-922,R.p[i*3+2]-94);if(d<bd){bd=d;bi=i}}g.placeCar(g.roadPoint(R,Math.max(0,bi-6)))}'''); time.sleep(8); shot('pit')
