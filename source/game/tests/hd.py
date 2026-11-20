pg.evaluate("localStorage.setItem('aurelia_qual','2')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=300000); pg.wait_for_function('window.__detail === 1', timeout=400000)
pg.click('button[data-mode="free"]'); time.sleep(2)
def near(name, x, y, tag, wait=5):
    pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', [name, x, -y]); time.sleep(wait); shot(tag)
near('Farm Road', 610, -850, 'H_village'); near('Street E-20', 300, 20, 'H_city')
