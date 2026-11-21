errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
pg.evaluate("localStorage.setItem('aurelia_mob','0'); localStorage.setItem('aurelia_qual','2'); localStorage.setItem('aurelia_tod','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
print('LIB', pg.evaluate("(()=>{const L=__game.FLO.lib.prop_tcar_a; return [L&&L[0]&&L[0].length, L&&L[1]&&L[1].length, L&&L[0]&&L[0].map(m=>m.material.name).join(',')]})()"))
pg.click('button[data-mode="free"]'); time.sleep(4); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')")
# park the player next to a Mira on a street, camera low and close
for i in range(3):
    r = pg.evaluate('''(()=>{const g=__game,L=g.LIFE; const cs=L.cars.filter(c=>c.k===0&&c.sx!==undefined); if(!cs.length) return null; const c=cs[%d %% cs.length];
      const fx=c.hx||1, fz=c.hz||0; g.placeCar({x:c.sx+fz*3.4-fx*6, y:g.hAt(c.sx+fz*3.4-fx*6,c.sz-fx*3.4-fz*6), z:c.sz-fx*3.4-fz*6, h:Math.atan2(fx,fz)}); window.__tgt=c; return [c.sx|0,c.sz|0, c.cur]})()''' % i)
    print('CAR', r); time.sleep(0.4)
    pg.evaluate('''(()=>{const c=__tgt, cam=__game.camera; window.__freeze=1; c.v=0; c.cur=0;})()''')
    time.sleep(1.5); shot('mira_%d' % i)
print('ERRS', errs)
