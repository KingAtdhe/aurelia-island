pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
def at(x, y, z, tx, tz, tag, wait=9):
    pg.evaluate('''([x,y,z,tx,tz])=>{__game.placeCar({x:x,y:y,z:z,h:Math.atan2(tx-x,tz-z)})}''', [x, y, z, tx, tz]); time.sleep(wait); shot(tag)
time.sleep(20); at(-2005, 1.75, 470, -2080, 476, 'co_fish'); at(-128, 1.8, 1404, -150, 1425, 'co_beach'); at(-450, 3.05, 405, -470, 520, 'co_kiosk'); at(60, 2.0, 448, 102, 500, 'co_marina', 12)
