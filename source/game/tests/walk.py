import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(6)
r = pg.evaluate('''()=>{const g=__game,L=g.LIFE,ws=g.W.walkways||[];let n=0,inB=0,onR=0,exB=[],exR=[];
 for(const w of ws){for(let t=0;t<=1;t+=0.1){for(const side of [-0.8,0,0.8]){let hx=w[2]-w[0],hz=w[3]-w[1];const hl=Math.hypot(hx,hz)||1;hx/=hl;hz/=hl;const x=w[0]+(w[2]-w[0])*t-hz*side,z=w[1]+(w[3]-w[1])*t+hx*side;n++;
  const c=g.obGrid.get(Math.floor(x/g.OG)+','+Math.floor(z/g.OG));if(c)for(const o of c.o){if(o.sp)continue;const dx=x-o[0],dz=z-o[1],cs=Math.cos(o[4]),sn=Math.sin(o[4]);if(Math.abs(dx*cs-dz*sn)<o[2]-0.2&&Math.abs(-dx*sn-dz*cs)<o[3]-0.2){inB++;if(exB.length<4)exB.push([x|0,z|0]);break}}
  const q=g.roadQuery(x,z,w[4],{});if(q.ok&&Math.abs(q.d)<q.road.hw-0.5&&q.road.type!=='dirt'){onR++;if(exR.length<4)exR.push([x|0,z|0,q.road.name,+q.d.toFixed(1)])}}}}
 return {ways:ws.length,walkers:L.walkers.length,samples:n,inBuilding:inB,onRoad:onR,exB,exR}}''')
print('WALK', json.dumps(r))
