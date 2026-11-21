import os
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
for nm, i, tag in [('Ring', 600, 'ring'), ('Street N0', 40, 'city')]:
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i))}''', [nm, i]); time.sleep(6)
    pg.evaluate("__game.inp.gas=1"); time.sleep(5); shot('d2_'+tag+'_1'); pg.evaluate("__game.inp.left=1"); time.sleep(0.8); shot('d2_'+tag+'_2'); pg.evaluate("__game.inp.left=0;__game.inp.right=1"); time.sleep(0.8); shot('d2_'+tag+'_3'); pg.evaluate("__game.inp.right=0;__game.inp.gas=0")
    print(tag, pg.evaluate("[__game.car.speed*3.6|0, __game.renderer.getPixelRatio()]"))
