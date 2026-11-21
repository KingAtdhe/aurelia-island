import json
pg.evaluate("localStorage.setItem('aurelia_qual','0'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(5)
r = pg.evaluate('''()=>{const g=__game,B=g.W.bounds;let best=[];for(let x=B[0]+200;x<B[1]-200;x+=40)for(let z=B[2]+200;z<B[3]-200;z+=40){
  let mn=1e9,mx=-1e9,ok=true;for(let dx=-120;dx<=120&&ok;dx+=20)for(let dz=-120;dz<=120;dz+=20){const G=g.ground(x+dx,z+dz,200);if(G.water||G.rq){ok=false;break}const y=g.hAt(x+dx,z+dz);mn=Math.min(mn,y);mx=Math.max(mx,y)}
  if(!ok)continue;const c=g.obGrid.get(Math.floor(x/g.OG)+','+Math.floor(z/g.OG));let obs=0;if(c){obs=c.o.length+c.c.length}best.push([mx-mn,obs,x,z])}
 best.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);return [B,best.slice(0,8)]}''')
print('FLAT', json.dumps(r))
