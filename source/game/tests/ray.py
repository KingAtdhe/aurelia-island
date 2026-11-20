pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
p = [45.75, 17.7, -155.14]
pg.evaluate('''([x,z])=>{let best=null,bd=1e9;for(const R of __game.roads){if(R.type!=='street')continue;for(let i=0;i<R.n;i++){const q=__game.roadPoint(R,i),d=Math.hypot(q.x-x,q.z-z);if(d<bd&&d>14){bd=d;best=[R,i]}}}__game.placeCar(__game.roadPoint(best[0],best[1]));}''', [p[0], p[2]]); time.sleep(1)
pg.evaluate("([x,z])=>{__game.car.h=Math.atan2(x-__game.car.x,z-__game.car.z)+0.35}", [p[0], p[2]]); time.sleep(6)
for sy in (0.25, 0.1, -0.05):
    print('RES', sy, pg.evaluate('''(sy)=>{const rc=new THREE.Raycaster();rc.setFromCamera(new THREE.Vector2(0,sy),__game.camera);const h=rc.intersectObjects(__game.scene.children,true).filter(i=>i.object.visible).slice(0,3);return h.map(i=>[i.object.name,i.object.material&&i.object.material.name,i.distance.toFixed(1),i.point.y.toFixed(1)])}''', sy))
