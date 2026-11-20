pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
def look(x, z, tag, dmin=28, dmax=60, wait=9):
    pg.evaluate('''([x,z,a,b])=>{let best=null,bd=1e9;for(const R of __game.roads){if(R.type==='circuit')continue;for(let i=0;i<R.n;i++){const q=__game.roadPoint(R,i),d=Math.hypot(q.x-x,q.z-z);if(d>a&&d<b&&Math.abs(d-(a+b)/2)<bd){bd=Math.abs(d-(a+b)/2);best=[R,i]}}}if(!best)return;__game.placeCar(__game.roadPoint(best[0],best[1]));__game.car.h=Math.atan2(x-__game.car.x,z-__game.car.z);}''', [x, z, dmin, dmax]); time.sleep(wait); shot(tag)
look(84.5, -734.1, 'wn_portal'); look(-1445.1, 785.3, 'wn_portal2'); look(1294.6, -641.5, 'wn_windpump'); look(808.0, -474.4, 'wn_lookout', 18, 40)
along = None
