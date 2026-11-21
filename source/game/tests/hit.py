import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
HIT = '''([sp])=>{const g=__game,c=g.car,a=g.FLO.data.instances[sp];let best=null;
 for(let i=0;i<a.length;i+=8){if(!(a[i+3]>0))continue;const q=g.roadQuery(a[i],a[i+2],a[i+1],{});if(q.ok&&Math.abs(q.d)<q.road.hw+4){best=i;break}}
 if(best===null)return 'none';const x=a[best],z=a[best+2],y=a[best+1],h=0.7;g.placeCar({x:x-Math.sin(h)*18,y:y,z:z-Math.cos(h)*18,h});
 let minD=1e9,maxSp=0;for(let s=0;s<240;s++){g.inp.gas=1;g.physics(1/60);const d=Math.hypot(c.x-x,c.z-z);minD=Math.min(minD,d);maxSp=Math.max(maxSp,c.speed*3.6)}
 g.inp.gas=0;return {sp,minDist:+minD.toFixed(2),endSpeed:c.speed*3.6|0,maxSp:maxSp|0,scale:a[best+3]}}'''
for sp in ['prop_lamp_city_hq', 'plane', 'spruce', 'prop_signal', 'prop_rk_cone', 'prop_bin', 'prop_bench_hq', 'rock', 'prop_tcar_a', 'prop_hydrant']:
    print('HIT', json.dumps(pg.evaluate(HIT, [sp])))
