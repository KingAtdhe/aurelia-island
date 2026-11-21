import json
exec(open('tests/lab.py').read().split("def J(")[0])
def J(s, a=None): return pg.evaluate(s, a) if a is not None else pg.evaluate(s)
pg.evaluate("window.__nocoll=false")
out = {}
# reverse from standstill, then forward again
out['reverse'] = J('''(()=>{L.flat(0,0);const g=__game,c=g.car;g.inp.brake=1;for(let i=0;i<120*4;i++)g.physics(1/120);const a=L.st();const fwd=c.vx*Math.sin(c.h)+c.vz*Math.cos(c.h);L.reset();g.inp.gas=1;for(let i=0;i<120*3;i++)g.physics(1/120);return {rev:a,revFwd:+fwd.toFixed(1),then:L.st()}})()''')
# standing start full lock and gas (donut test) — must not explode
out['donut'] = J('''(()=>{L.flat(0,0);const g=__game,c=g.car;let my=0;for(let i=0;i<120*5;i++){g.inp.left=1;g.inp.gas=1;g.physics(1/120);my=Math.max(my,Math.abs(c.yr))}const s=L.st();L.reset();return {maxYr:+my.toFixed(2),end:s}})()''')
# walls: drive straight into a building box and a lamp
out['wall'] = J('''(()=>{const g=__game,c=g.car;let tgt=null;for(const cell of g.obGrid.values()){for(const o of cell.o){if(!o.sp&&o[2]>6&&o[3]>6){tgt=o;break}}if(tgt)break}
  const h=Math.atan2(tgt[0]-(tgt[0]-40),0);g.placeCar({x:tgt[0],y:g.hAt(tgt[0],tgt[1]-tgt[3]-35),z:tgt[1]-Math.max(tgt[2],tgt[3])-35,h:0});c.vz=80/3.6;c.vx=0;c.gear=2;
  let minS=1e9,t=0,inside=false;for(let i=0;i<120*3;i++){g.inp.gas=1;g.physics(1/120);const dx=c.x-tgt[0],dz=c.z-tgt[1],cs=Math.cos(tgt[4]),sn=Math.sin(tgt[4]);if(Math.abs(dx*cs-dz*sn)<tgt[2]-0.5&&Math.abs(-dx*sn-dz*cs)<tgt[3]-0.5)inside=true}
  L.reset();return {inside,end:L.st()}})()''')
# glancing hit: approach box at 20 degrees
out['glance'] = J('''(()=>{const g=__game,c=g.car;let tgt=null;for(const cell of g.obGrid.values()){for(const o of cell.o){if(!o.sp&&o[2]>8&&o[3]>8&&Math.abs(o[4])<0.01){tgt=o;break}}if(tgt)break}
  if(!tgt)return 'none';const z0=tgt[1]-tgt[3]-12;g.placeCar({x:tgt[0]-14,y:g.hAt(tgt[0]-14,z0),z:z0,h:0.35});c.vx=Math.sin(0.35)*60/3.6;c.vz=Math.cos(0.35)*60/3.6;c.gear=1;let my=0;
  for(let i=0;i<120*2;i++){g.physics(1/120);my=Math.max(my,Math.abs(c.yr))}L.reset();return {maxYr:+my.toFixed(2),end:L.st()}})()''')
print('EDGE', json.dumps(out))
