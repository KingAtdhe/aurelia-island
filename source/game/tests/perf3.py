import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i))}''', ['Street N0', 40]); time.sleep(8)
r = pg.evaluate('''()=>{const F=__game.FLO,S={},cam=__game.camera;let cells=0,vis=0;for(const c of F.cells.values()){cells++;for(const k in c.g){const G=c.g[k];if(!G.visible)continue;vis++;G.children.forEach(im=>{const sp=(im.geometry.name||'')+'|'+im.material.name;const key=k+' '+im.material.name;const s=S[key]||(S[key]=[0,0]);s[0]++;s[1]+=(im.geometry.index?im.geometry.index.count/3:0)*im.count})}}
 const sp={};for(const c of F.cells.values()){for(const g in c.it){for(const s in c.it[g]){const k=g+':'+s;sp[k]=(sp[k]||0)+c.it[g][s].length}}}
 const tri={};for(const s in F.lib){const L=F.lib[s];tri[s]=[0,1].map(l=>(L[l]||[]).reduce((a,pm)=>a+(pm.geometry.index?pm.geometry.index.count/3:0),0)).concat([(L[0]||[]).length])}
 return {size:F.size,cells,vis,top:Object.entries(S).sort((a,b)=>b[1][0]-a[1][0]).slice(0,15),sp:Object.entries(sp).sort((a,b)=>b[1]-a[1]).slice(0,40),tri:Object.entries(tri).sort((a,b)=>b[1][0]-a[1][0]).slice(0,25)}}''')
print('size',r['size'],'cells',r['cells'],'visible groups',r['vis'])
for k,v in r['top']: print('  grp', v, k)
print('species counts'); print(r['sp'])
print('tris lod0/lod1/prims'); print(r['tri'])
