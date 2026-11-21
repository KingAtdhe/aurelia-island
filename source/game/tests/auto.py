import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','0'); localStorage.setItem('aurelia_tod','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(12)
pg.evaluate("document.querySelectorAll('#help').forEach(e=>e.style.display='none')")
# autopilot: aim at a point 18 m ahead on the current road, log anomalies every frame
pg.evaluate('''()=>{const g=__game;window.__log=[];window.__toasts=[];const T=document.getElementById('toast');new MutationObserver(()=>__toasts.push(T.textContent)).observe(T,{childList:true,characterData:true,subtree:true});
 window.__ap=(name,i0)=>{const R=g.roads.find(r=>r.name===name);g.placeCar(g.roadPoint(R,i0));window.__apR=R;window.__apT=0;window.__apMax=0;window.__apStuck=0;};
 const tick=()=>{requestAnimationFrame(tick);const R=window.__apR;if(!R)return;const c=g.car,q=g.roadQuery(c.x,c.z,c.y,{});
  if(q.ok&&q.road===R){let j=Math.min(R.n-1,q.i+Math.ceil(18/(R.step||4)));if(R.closed)j=(q.i+Math.ceil(18/(R.step||4)))%R.n;const p=R.p,tx=p[j*3]-c.x,tz=p[j*3+2]-c.z;let dh=Math.atan2(tx,tz)-c.h;while(dh>Math.PI)dh-=2*Math.PI;while(dh<-Math.PI)dh+=2*Math.PI;
   g.inp.left=dh>0.04?1:0;g.inp.right=dh<-0.04?1:0;const want=Math.abs(dh)>0.35?14:30;g.inp.gas=c.speed<want?1:0;g.inp.brake=c.speed>want+4?1:0;}
  else{g.inp.gas=1;g.inp.left=g.inp.right=0}
  const G=g.ground(c.x,c.z,c.y+1);__apT++;__apMax=Math.max(__apMax,c.speed*3.6);
  if(c.y<G.y-0.5)__log.push(['below',R.name,c.x|0,c.z|0,+(G.y-c.y).toFixed(1)]);
  if(c.air&&c.vy<-15)__log.push(['fall',R.name,c.x|0,c.z|0]);
  if(g.inp.gas&&c.speed<0.5&&__apT>60){if(++__apStuck==90)__log.push(['stuck',R.name,c.x|0,c.z|0]);}else __apStuck=0;
  if(q.ok&&Math.abs(q.d)>q.road.hw+1.5&&q.road===R)__log.push(['offroad',R.name,c.x|0,c.z|0,+q.d.toFixed(1)]);};tick();}''')
roads = pg.evaluate("__game.roads.filter(r=>r.n>40).map(r=>r.name)")
seen=set(); test=[r for r in roads if not (r in seen or seen.add(r))][:22]
for nm in test:
    pg.evaluate("n=>{__log.length=0;__toasts.length=0;__ap(n,Math.floor(__game.roads.find(r=>r.name===n).n*0.2))}", nm); time.sleep(25)
    L = pg.evaluate("(()=>{const c={};for(const e of __log){c[e[0]]=(c[e[0]]||0)+1}return {c,first:__log.slice(0,3),toasts:[...new Set(__toasts)].slice(0,4),max:__apMax|0,frames:__apT}})()")
    print('RUN', nm, json.dumps(L)); shot('au_'+nm.replace(' ','_'))
