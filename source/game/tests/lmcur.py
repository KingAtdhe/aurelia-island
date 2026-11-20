pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(25)
pg.evaluate("document.querySelectorAll('#help,#toast,.ctl,#modes,#opts').forEach(e=>e.style.display='none')")
def look(lx, lz, D, tag, wait=10):
    pg.evaluate('''([lx,lz,D])=>{const G=__game;let b=null,bd=1e12;const rt=Math.atan2(0,1);
      for(const r of G.roads){for(let i=2;i<r.n-2;i++){if(r.wall[i])continue;const x=r.p[i*3],z=r.p[i*3+2];const d=Math.abs(Math.hypot(x-lx,z-lz)-D);if(d<bd){bd=d;b=G.roadPoint(r,i);}}}
      b.h=Math.atan2(lx-b.x,lz-b.z);G.placeCar(b);}''', [lx, lz, D]); time.sleep(wait); shot(tag)
import os
for i, spec in enumerate(os.environ.get('LMS', '').split(';')):
    if spec: x, z, D = map(float, spec.split(',')); look(x, z, D, 'lm_%d' % i)
