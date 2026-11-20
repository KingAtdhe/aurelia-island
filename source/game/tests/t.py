pg.wait_for_function('window.__detail === 1', timeout=180000)
pg.evaluate("localStorage.setItem('aurelia_qual','2')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=120000); pg.wait_for_function('window.__detail === 1', timeout=180000)
pg.click('button[data-mode="free"]'); time.sleep(2)
pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', ['Lake Trail', -1420, -290]); time.sleep(3.5)
print('with shadows', pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
pg.evaluate("__game.scene.children.forEach(o=>{if(o.isDirectionalLight)o.castShadow=false})"); time.sleep(1.5)
print('no shadows', pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
print(pg.evaluate('''()=>{const g=__game,cam=g.camera,fr=new THREE.Frustum(),M=new THREE.Matrix4();M.multiplyMatrices(cam.projectionMatrix,cam.matrixWorldInverse);fr.setFromProjectionMatrix(M);const S={};
g.scene.traverseVisible(o=>{if(!o.isMesh)return;const geo=o.geometry;const t=(geo.index?geo.index.count:geo.attributes.position.count)/3*(o.isInstancedMesh?o.count:1);
if(!o.isInstancedMesh&&o.frustumCulled){if(!geo.boundingSphere)geo.computeBoundingSphere();const s=geo.boundingSphere.clone().applyMatrix4(o.matrixWorld);if(!fr.intersectsSphere(s))return;}
const k=(o.isInstancedMesh?'I:':'')+(o.name||o.material.name).split(/__|_\\d|\\./)[0];S[k]=(S[k]||0)+t});return JSON.stringify(Object.entries(S).sort((a,b)=>b[1]-a[1]).slice(0,18).map(e=>[e[0],Math.round(e[1])]))}'''))
