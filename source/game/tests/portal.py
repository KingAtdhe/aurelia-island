pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
import math
for k, (x, y, z, a) in enumerate(((84.5, 114.7, -734.1, 2.6), (-1445.1, 63.0, 785.3, 5.4), (-1524.9, 61.4, 682.7, 2.2))):
    dx, dz = math.cos(a), -math.sin(a); cx, cz = x + dx * 32, z + dz * 32
    pg.evaluate("([x,y,z,h])=>{__game.placeCar({x:x,y:y,z:z,h:h})}", [cx, y + 0.3, cz, math.atan2(x - cx, z - cz)]); time.sleep(8); shot('pt_%d' % k)
