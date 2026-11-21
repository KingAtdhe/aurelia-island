errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
pg.evaluate("localStorage.setItem('aurelia_mob','0'); localStorage.setItem('aurelia_qual','2'); localStorage.setItem('aurelia_tod','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(4); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')")
# freeze traffic and look at a Mira from the roadside with the game's own camera placed by hand
for i in range(4):
    r = pg.evaluate('''(()=>{const g=__game,L=g.LIFE; const cs=L.cars.filter(c=>c.k===0&&c.sx!==undefined); const c=cs[(%d*7) %% cs.length]; window.__tgt=c; L.cars.forEach(o=>{o.v=0;o.cur=0});
      const fx=c.hx, fz=c.hz; g.placeCar({x:c.sx-fz*9, y:g.hAt(c.sx-fz*9,c.sz+fx*9), z:c.sz+fx*9, h:Math.atan2(fx,fz)}); return [c.sx|0,c.sz|0]})()''' % i)
    time.sleep(1.2)
    pg.evaluate('''(()=>{const g=__game,c=__tgt,cam=g.camera; window.__camHold=1; const a=%f; const fx=c.hx,fz=c.hz; const px=c.sx+fx*Math.cos(a)*5.2-fz*Math.sin(a)*5.2, pz=c.sz+fz*Math.cos(a)*5.2+fx*Math.sin(a)*5.2;
      const y=g.hAt(c.sx,c.sz); cam.position.set(px, y+1.35, pz); cam.lookAt(c.sx, y+0.6, c.sz); cam.updateMatrixWorld();})()''' % [0.7, 2.4, -0.8, 1.57][i])
    time.sleep(1.5); pg.screenshot(path='shots/mira2_%d.jpg' % i, quality=90)
print('ERRS', errs)
