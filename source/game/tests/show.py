pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(2)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
def near(name, x, y, tag, wait=6):
    pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', [name, x, -y]); time.sleep(wait); shot(tag)
near('Street E-20', 300, 20, 'S_city'); near('Farm Road', 610, -850, 'S_village'); near('Ring', -1640, -520, 'S_coast'); near('Lake Trail', -1420, 290, 'S_forest'); near('Farm Road', 560, -800, 'S_village2')
