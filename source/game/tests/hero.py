pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
pts = pg.evaluate('''()=>{const out=[];__game.scene.traverse(o=>{if(o.isMesh&&o.material&&o.material.name==='HeroSigns'){o.updateMatrixWorld(true);const b=new THREE.Box3().setFromObject(o);const c=new THREE.Vector3();b.getCenter(c);const s=new THREE.Vector3();b.getSize(s);out.push([c.x,c.y,c.z,s.x,s.z])}});return out}''')
print('RES', len(pts), pts[:6])
for k, p in enumerate(pts[4:8]):
    pg.evaluate('''([x,z])=>{let best=null,bd=1e9;for(const R of __game.roads){if(R.type!=='street')continue;for(let i=0;i<R.n;i++){const q=__game.roadPoint(R,i),d=Math.hypot(q.x-x,q.z-z);if(d<bd&&d>18){bd=d;best=[R,i]}}}__game.placeCar(__game.roadPoint(best[0],best[1]));}''', [p[0], p[2]]); time.sleep(1)
    pg.evaluate("([x,z])=>{__game.car.h=Math.atan2(x-__game.car.x,z-__game.car.z)+0.35}", [p[0], p[2]]); time.sleep(6); shot('HB%d' % k)
