import math
pg.evaluate("localStorage.setItem('aurelia_qual','2')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=120000)
pg.click('button[data-mode="free"]'); time.sleep(2)
print('qual', pg.evaluate("document.getElementById('oQual').textContent"))
def near(name, x, y, tag, q=None):
    if q is not None: pg.evaluate("q=>{localStorage.setItem('aurelia_qual',q)}", q)
    i = pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b));return b}''', [name, x, -y]); time.sleep(3.5); shot(tag)
    print(tag, i, pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
near('Lake Trail', -1420, 290, 'g_forest'); near('Pine Trail', -1500, 600, 'g_forest2'); near('Farm Road', 625, -855, 'g_village'); near('Street E-20', 100, -20, 'g_city'); near('Ring', -1640, -520, 'g_coast'); near('Skyline Road', 0, 900, 'g_mtn')
pg.click('#bMenu'); time.sleep(.3); pg.click('#oTime'); time.sleep(.3); pg.click('button[data-mode="free"]'); time.sleep(1); near('Street E-20', 100, -20, 'g_night')
