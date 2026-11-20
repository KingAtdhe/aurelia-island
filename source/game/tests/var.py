pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
print('RES', pg.evaluate("()=>[__life.carMesh.length, __life.walkMesh.map(w=>w.length).join(','), __life.cars.length]"))
def near(name, x, y, tag, wait=6):
    pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', [name, x, -y]); time.sleep(wait); shot(tag)
near('Street E-20', 300, 20, 'V_city'); near('Ring', -1640, -520, 'V_coast')
pg.evaluate("()=>{for(let i=0;i<300;i++) __life.step(0.05)}")
near('Street E-20', 380, 20, 'V_city2')
