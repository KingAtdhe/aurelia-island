import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_tod','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(6); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')")
st = pg.evaluate('''()=>{const g=__game,o={};for(const r of g.roads)if(r.lim){let c=0,rl=0;for(const L of r.lim)for(let i=0;i<r.n;i++){if(L[i]>0&&L[i]<r.hw+1)c++;else if(L[i]>0)rl++}o[r.name]=[c,rl,r.n]}return o}''')
print('LIM', json.dumps(st))
r = pg.evaluate('''()=>{const g=__game,c=g.car;for(const R of g.roads){if(!R.lim||!/Ring|Peninsula|Canyon|Lighthouse/.test(R.name))continue;for(let i=10;i<R.n-10;i++)for(const si of [0,1])if(R.lim[si][i]>R.hw+1&&R.lim[si][i-3]>0&&R.lim[si][i+3]>0){
   const p=g.roadPoint(R,i);const q=g.roadQuery(p.x,p.z,p.y,{});const tgt=si===0?1:-1;
   // heading toward that side: side vector (tz,-tx)*tgt
   const vx=q.tz*tgt,vz=-q.tx*tgt;p.h=Math.atan2(vx*0.7+q.tx*0.7,vz*0.7+q.tz*0.7);g.placeCar(p);let maxd=0;
   for(let s=0;s<240;s++){g.inp.gas=1;g.physics(1/60);const qq=g.roadQuery(c.x,c.z,c.y,{});if(qq.ok)maxd=Math.max(maxd,Math.abs(qq.d))}g.inp.gas=0;
   return {road:R.name,i,lim:+R.lim[si][i].toFixed(1),maxd:+maxd.toFixed(1),end:c.speed*3.6|0}}}return 'none'}''')
print('RAIL', json.dumps(r)); time.sleep(5); shot('rail')
