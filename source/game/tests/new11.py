import os
pg.evaluate("localStorage.setItem('aurelia_qual','2')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(25)
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
def at(name, idx, tag, h=0, wait=10):
    pg.evaluate('''([n,i,h])=>{const R=__game.roads.find(r=>r.name===n);const p=__game.roadPoint(R,i);p.h+=h;__game.placeCar(p)}''', [name, idx, h]); time.sleep(wait); shot(tag)
for spec in os.environ['SPOTS'].split(';'):
    n, i, h, tag = spec.split(','); at(n, int(i), tag, float(h))
