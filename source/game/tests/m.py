import math
pg.wait_for_function('window.__detail === 1', timeout=180000); print('detail streamed')
def near(name, x, y, tag, wait=3.5):
    pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', [name, x, -y]); time.sleep(wait); shot(tag)
    print(tag, pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
for q in ('1', '2'):
    pg.evaluate("q=>localStorage.setItem('aurelia_qual',q)", q); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=120000); pg.wait_for_function('window.__detail === 1', timeout=180000)
    pg.click('button[data-mode="free"]'); time.sleep(2); print('qual', pg.evaluate("document.getElementById('oQual').textContent"), 'shadows', pg.evaluate('__game.scene.children.some(o=>o.isDirectionalLight&&o.castShadow)'))
    near('Street E-20', 100, -20, 'm_city_q' + q); near('Lake Trail', -1420, 290, 'm_forest_q' + q)
pg.evaluate("()=>{const g=__game;g.camera.position.set(g.car.x+4.2*Math.sin(g.car.h+0.9),g.car.y+1.6,g.car.z+4.2*Math.cos(g.car.h+0.9));}")
