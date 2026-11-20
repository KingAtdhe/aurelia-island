pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
print(pg.evaluate("__game.roads.map(r=>r.name+':'+(r.kind||r.type||'')+':'+r.n).join(' | ')"))
def along(name, frac, tag, h=0, wait=8):
    pg.evaluate('''([n,f])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,Math.floor(R.n*f)))}''', [name, frac]); time.sleep(1)
    if h: pg.evaluate("h=>{__game.car.h+=h}", h)
    time.sleep(wait); shot(tag)
import os
for i, spec in enumerate(os.environ.get('SPOTS', '').split(';')):
    if spec: n, f = spec.rsplit(',', 1); along(n, float(f), 'rc_%d' % i)
