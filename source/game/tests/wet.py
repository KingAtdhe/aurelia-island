import os
pg.evaluate("localStorage.setItem('aurelia_qual','2'); localStorage.setItem('aurelia_tod', os_tod); localStorage.setItem('aurelia_night', os_n); localStorage.setItem('aurelia_wet', os_w)".replace('os_tod', os.environ.get('TOD','2')).replace('os_n', 'true' if os.environ.get('TOD','2')=='2' else 'false').replace('os_w', os.environ.get('WET','0'))); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(25)
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
def at(name, idx, tag, h=0, wait=10):
    pg.evaluate('''([n,i,h])=>{const R=__game.roads.find(r=>r.name===n);const p=__game.roadPoint(R,i);p.h+=h;__game.placeCar(p)}''', [name, idx, h]); time.sleep(wait); shot(tag)
P=os.environ.get('PFX','wet')
at('Street N0', 40, P+'_city'); at('Street E-160', 120, P+'_old'); at('Summit Pass', 60, P+'_mtn'); at('Ring', 600, P+'_ring')
