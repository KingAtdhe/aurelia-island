pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
def along(name, frac, tag, h=0, wait=8):
    pg.evaluate('''([n,f])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,Math.floor(R.n*f)))}''', [name, frac]); time.sleep(1)
    if h: pg.evaluate("h=>{__game.car.h+=h}", h)
    time.sleep(wait); shot(tag)
along('Summit Pass', 0.35, 'wc_pass', 0.3); along('Eagle Descent', 0.5, 'wc_descent'); along('Canyon Road', 0.5, 'wc_canyon'); along('Mesa Road', 0.4, 'wc_mesa', 0.4)
