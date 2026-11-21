import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(6)
print('SIDE', json.dumps(pg.evaluate('''()=>{const g=__game,R=g.roads.find(r=>r.name==='Summit Pass'),i=61,p=R.p,x=p[i*3],y=p[i*3+1],z=p[i*3+2];
 const q=g.roadQuery(x+0.01,z,y,{});const out={y,cut0:R.cut[0][i],cut1:R.cut[1][i],tx:q.tx,tz:q.tz};
 for(const d of [-31,-18,-8,-3,3,8,18,31]){const px=x+q.tz*d,pz=z-q.tx*d;const qq=g.roadQuery(px,pz,y,{});out['h'+d]=+(g.hAt(px,pz)-y).toFixed(1);out['dq'+d]=qq.ok?+qq.d.toFixed(1):null}
 let n0=0,n1=0;for(const r of g.roads)if(r.cut){n0+=r.cut[0].reduce((a,b)=>a+b,0);n1+=r.cut[1].reduce((a,b)=>a+b,0)}out.n=[n0,n1];return out}''')))
