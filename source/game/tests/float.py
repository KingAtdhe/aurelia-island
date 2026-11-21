import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
r = pg.evaluate('''()=>{const g=__game,D=g.FLO.data,res={};
 for(const sp in D.instances){if(/^(prop_walker|prop_tcar_|prop_sail|prop_motor|prop_fishing|prop_rowing)/.test(sp))continue;const a=D.instances[sp];let n=0,fl=0,sk=0,ex=null,ex2=null;
  for(let i=0;i<a.length;i+=8){if(!(a[i+3]>0))continue;const G=g.ground(a[i],a[i+2],a[i+1]+2);if(G.water)continue;n++;const d=a[i+1]-G.y;
   if(d>0.35){fl++;if(!ex||d>ex[2])ex=[a[i]|0,a[i+2]|0,+d.toFixed(2),G.surf]} if(d<-0.6){sk++;if(!ex2||d<ex2[2])ex2=[a[i]|0,a[i+2]|0,+d.toFixed(2),G.surf]}}
  if(fl||sk)res[sp]=[n,fl,sk,ex,ex2]}
 return res}''')
for k, v in sorted(r.items(), key=lambda kv: -(kv[1][1] + kv[1][2]))[:40]:
    print('FLT %-24s n %6d float %5d sunk %5d  worst-float %s worst-sunk %s' % (k, v[0], v[1], v[2], v[3], v[4]))
