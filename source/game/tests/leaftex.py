import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_tod','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(5)
pg.evaluate('''([n])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,Math.floor(R.n*0.35)))}''', ['Serpentine']); time.sleep(5)
print('TEX', json.dumps(pg.evaluate('''()=>{let m=null,inst=null;__game.scene.traverse(o=>{if(!m&&o.isInstancedMesh&&o.material&&o.material.name==='LeavesHQ'&&/spruce/.test(o.name)){m=o.material;inst=o}});if(!m)return 'none';
 const img=m.map.image,cv=document.createElement('canvas');cv.width=256;cv.height=256;const g=cv.getContext('2d');g.drawImage(img,0,0,256,256);const d=g.getImageData(0,0,256,256).data;let r=0,gg=0,b=0,n=0;for(let i=0;i<d.length;i+=4){if(d[i+3]>128){r+=d[i];gg+=d[i+1];b+=d[i+2];n++}}
 const ic=inst.instanceColor?[...inst.instanceColor.array.slice(0,9)].map(v=>+v.toFixed(2)):null;const geo=inst.geometry;const ca=geo.attributes.color?[...geo.attributes.color.array.slice(0,6)].map(v=>+(+v).toFixed(2)):null;
 return {avg:[r/n|0,gg/n|0,b/n|0],cover:+(n/65536).toFixed(2),enc:m.map.encoding,ic,ca,caNorm:geo.attributes.color&&geo.attributes.color.normalized,caType:geo.attributes.color&&geo.attributes.color.array.constructor.name,cast:inst.castShadow,recv:inst.receiveShadow}}''')))
