pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(25)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
def at(name, idx, tag, h=0, wait=9):
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i))}''', [name, idx]); time.sleep(1)
    if h: pg.evaluate("h=>{__game.car.h+=h}", h)
    time.sleep(wait); shot(tag)
at('Ring', 600, 'rn_ring'); at('Ring', 194, 'rn_works'); at('Summit Pass', 158, 'rn_chev'); at('Mesa Roundabout', 2, 'rn_rbt')
at('Street N-320', 70, 'rn_setts'); at('Lake Trail', 100, 'rn_track'); at('Farm Road', 100, 'rn_country')
