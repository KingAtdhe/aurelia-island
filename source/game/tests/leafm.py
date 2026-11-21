import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_tod','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(5)
pg.evaluate('''([n])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,Math.floor(R.n*0.35)))}''', ['Serpentine']); time.sleep(6)
print('LM', json.dumps(pg.evaluate('''()=>{const out={};__game.scene.traverse(o=>{if(!o.isMesh||!o.visible)return;const m=o.material;if(!m||!/Leaves|TreeCards/.test(m.name))return;const k=m.name+'|'+o.type+'|'+(o.name||'').slice(0,20);if(out[k])return;
 out[k]={col:m.color.toArray().map(v=>+v.toFixed(2)),em:m.emissive.toArray().map(v=>+v.toFixed(2)),ei:m.emissiveIntensity,map:!!m.map,emap:!!m.emissiveMap,vc:m.vertexColors,mapImg:m.map&&m.map.image?[m.map.image.width,m.map.image.height]:null,lights:m.lights,type:m.type,side:m.side,at:m.alphaTest}});return out}''')))
