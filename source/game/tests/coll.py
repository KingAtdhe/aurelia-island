import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
r = pg.evaluate('''()=>{const g=__game,F=g.FLO,D=F.data,OG=g.OG,res={};
 const hit=(x,z)=>{const c=g.obGrid.get(Math.floor(x/OG)+','+Math.floor(z/OG));if(!c)return false;
   for(const o of c.c)if(Math.hypot(x-o[0],z-o[1])<o[2]+0.6)return true;if(c.k)for(const o of c.k)if(Math.hypot(x-o[0],z-o[1])<o[2]+0.6)return true;
   for(const o of c.o){const dx=x-o[0],dz=z-o[1],cs=Math.cos(o[4]),sn=Math.sin(o[4]),lx=dx*cs-dz*sn,ly=-dx*sn-dz*cs;if(Math.abs(lx)<o[2]+0.6&&Math.abs(ly)<o[3]+0.6)return true}return false};
 for(const sp in D.instances){if(/^(grass|flowers|prop_walker|prop_tcar)/.test(sp))continue;const a=D.instances[sp];let near=0,miss=0,ex=null;
  for(let i=0;i<a.length;i+=8){const x=a[i],z=a[i+2],q=g.roadQuery(x,z,a[i+1],{});if(!q.ok)continue;const e=Math.abs(q.d)-q.road.hw;if(e>5||e<-0.5&&!/rk_|cone|barrier/.test(sp))continue;near++;if(!hit(x,z)){miss++;if(!ex)ex=[x|0,z|0,+e.toFixed(1),q.road.name]}}
  if(near)res[sp]=[near,miss,ex]}
 return {res,circles:g.W.circles.length,boxes:g.W.obstacles.length}}''')
print('COLL', r['circles'], r['boxes'])
print('TOTAL near', sum(v[0] for v in r['res'].values()), 'missing', sum(v[1] for v in r['res'].values()))
for k, v in sorted(r['res'].items(), key=lambda kv: -kv[1][1])[:12]:
    print('  %-26s near %5d  no-collider %5d  e.g. %s' % (k, v[0], v[1], v[2]))
