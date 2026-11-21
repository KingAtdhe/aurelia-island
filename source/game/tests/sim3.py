import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','0'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
SIM = '''([name, secs, wantK])=>{const g=__game,c=g.car,R=g.roads.find(r=>r.name===name);g.placeCar(g.roadPoint(R,Math.floor(R.n*0.1)));
 const log=[],dt=1/60;let max=0,stuck=0,dist=0,px=c.x,pz=c.z,resets=0,maxOff=0;
 for(let s=0;s<secs*60;s++){const q=g.roadQuery(c.x,c.z,c.y,{});
  if(q.ok&&q.road===R){const st=Math.max(1,Math.ceil(16/(R.step||4)));let j=R.closed?(q.i+st)%R.n:Math.min(R.n-1,q.i+st);if(!R.closed&&j>=R.n-2)break;
   const p=R.p,tx=p[j*3]-c.x,tz=p[j*3+2]-c.z;let dh=Math.atan2(tx,tz)-c.h;while(dh>Math.PI)dh-=2*Math.PI;while(dh<-Math.PI)dh+=2*Math.PI;
   g.inp.left=dh>0.03?1:0;g.inp.right=dh<-0.03?1:0;const want=(Math.abs(dh)>0.3?13:Math.abs(dh)>0.12?22:38)*wantK;g.inp.gas=c.speed<want?1:0;g.inp.brake=c.speed>want+3?1:0;maxOff=Math.max(maxOff,Math.abs(q.d)-q.road.hw);}
  else{g.inp.gas=0;g.inp.brake=1;g.inp.left=g.inp.right=0;if(!q.ok||q.road!==R){log.push(['lost',c.x|0,c.z|0,q.ok?q.road.name:'-']);break}}
  const y0=c.y; g.physics(dt); const G=g.ground(c.x,c.z,c.y+1);
  if(c.sink>0){log.push(['sink',c.x|0,c.z|0]);break}
  if(Math.hypot(c.x-px,c.z-pz)>5){resets++;log.push(['jump',c.x|0,c.z|0])}
  dist+=Math.hypot(c.x-px,c.z-pz);px=c.x;pz=c.z;max=Math.max(max,c.speed*3.6);
  if(!c.air&&c.y<G.y-0.3)log.push(['below',c.x|0,c.z|0]);
  if(c.air&&c.vy<-12)log.push(['fall',c.x|0,c.z|0,c.vy|0]);
  if(Math.abs(c.pitch)>0.5||Math.abs(c.roll)>0.5)log.push(['tilt',c.x|0,c.z|0,+c.pitch.toFixed(2),+c.roll.toFixed(2)]);
  if(g.inp.gas&&c.speed<0.4&&s>120){if(++stuck==120)log.push(['stuck',c.x|0,c.z|0])}else stuck=0;}
 g.inp.gas=g.inp.brake=g.inp.left=g.inp.right=0;const cnt={};for(const e of log)cnt[e[0]]=(cnt[e[0]]||0)+1;
 return {dist:dist|0,max:max|0,maxOff:+maxOff.toFixed(1),cnt,first:log.slice(0,3)}}'''
roads = pg.evaluate("[...new Set(__game.roads.filter(r=>r.n>30).map(r=>r.name))]")
print('NROADS', len(roads))
bad = 0
for nm in roads:
    r = pg.evaluate(SIM, [nm, 60, 0.75])
    flag = r['cnt'] or r['maxOff'] > 1.5
    if flag: bad += 1
    print('SIM' + ('!' if flag else ' '), nm, json.dumps(r))
print('BAD', bad)
print('HITS', pg.evaluate("(()=>{let k=0,n=0;for(const c of __game.obGrid.values())if(c.k)for(const o of c.k){n++;if(o.dead)k++}return [k,n]})()"))
