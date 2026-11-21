import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(6)
r = pg.evaluate('''()=>{const g=__game,L=g.LIFE;if(!L.ready)return 'not ready';const car=g.car;car.x=99999;car.z=99999;   // player out of the way
 const ev={overlap:0,overlapEx:[],stop:0,lane:0,laneEx:[],jump:0},N=L.cars.length;const last=L.cars.map(c=>[c.sx,c.sz]);
 const stillT=new Float32Array(N);let maxStill=0;for(let s=0;s<60*240;s++){g.updateLife(1/60);for(let k=0;k<N;k++){const c=L.cars[k];stillT[k]=c.cur<0.2?stillT[k]+1/60:0;maxStill=Math.max(maxStill,stillT[k])}
  if(s%30==0){for(let a=0;a<N;a++){const A=L.cars[a];if(A.sx===undefined)continue;for(let b=a+1;b<N;b++){const B=L.cars[b];if(B.sx===undefined)continue;const d=Math.hypot(A.sx-B.sx,A.sz-B.sz);if(d<2.2){ev.overlap++;if(ev.overlapEx.length<5)ev.overlapEx.push([A.sx|0,A.sz|0,A.r.name,B.r.name,+d.toFixed(1)])}}
    const q=g.roadQuery(A.sx,A.sz,A.r.p[Math.floor(A.s)*3+1],{});if(q.ok&&Math.abs(q.d)>q.road.hw+0.5){ev.lane++;if(ev.laneEx.length<4)ev.laneEx.push([A.sx|0,A.sz|0,A.r.name,+q.d.toFixed(1),q.road.name])}}}
 }
 let still=0;for(const c of L.cars)if(c.cur<0.3)still++;return {N,ev,still,maxStill:+maxStill.toFixed(1),longStill:[...stillT].filter(v=>v>40).length}}''')
print('TRAF', json.dumps(r))
