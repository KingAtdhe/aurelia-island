pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts,#hud,#mini,.hud').forEach(e=>e.style.display='none')")
def look(x, y, tag, wait=9):
    pg.evaluate('''([x,z])=>{let best=null,bd=1e9;for(const R of __game.roads){if(R.type==='circuit')continue;for(let i=0;i<R.n;i+=2){const q=__game.roadPoint(R,i),d=Math.hypot(q.x-x,q.z-z);if(d<bd&&d>25){bd=d;best=[R,i]}}}__game.placeCar(__game.roadPoint(best[0],best[1]));__game.car.h=Math.atan2(x-__game.car.x,z-__game.car.z);}''', [x, -y]); time.sleep(wait); shot(tag)
look(190, -470, 'co_marina'); look(-2065, -476, 'co_fish'); look(-170, -1419, 'co_beach'); look(-462, -418, 'co_kiosk')
