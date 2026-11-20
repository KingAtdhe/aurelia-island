import os
pg.evaluate("localStorage.setItem('aurelia_qual', os_q)".replace('os_q', os.environ.get('Q', '2'))); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(25)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts,#mini,.pad,#hud,#reg,#spd,#top').forEach(e=>e.style.display='none')")
if os.environ.get('JS'): pg.evaluate(os.environ['JS'])
def at(name, idx, tag, h=0, wait=9):
    pg.evaluate('''([n,i,h])=>{const R=__game.roads.find(r=>r.name===n);const p=__game.roadPoint(R,i);p.h+=h;__game.placeCar(p)}''', [name, idx, h]); time.sleep(wait); shot(tag)
P = os.environ.get('PFX', 'lk')
at('Street N0', 40, P + '_city'); at('Ring', 600, P + '_coast'); at('Summit Pass', 120, P + '_mtn'); at('Farm Road', 100, P + '_farm'); at('Street E-160', 120, P + '_old'); at('Dune Road', 60, P + '_desert')
