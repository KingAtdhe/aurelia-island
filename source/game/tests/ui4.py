pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
for k in range(3):
    print('POS', k, pg.evaluate("[__game.car.x|0,__game.car.z|0,(__game.car.speed*3.6)|0]")); time.sleep(2)
p0 = pg.evaluate("[__game.car.x|0,__game.car.z|0]"); pg.click('#bMenu'); time.sleep(3); p1 = pg.evaluate("[__game.car.x|0,__game.car.z|0]"); pg.click('#bResume'); time.sleep(0.3); p2 = pg.evaluate("[__game.car.x|0,__game.car.z|0]")
print('MENU', p0, p1, p2)
