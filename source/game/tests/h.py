for q in (0, 1):
    pg.evaluate("q=>localStorage.setItem('aurelia_qual',q)", str(q)); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=120000)
    pg.click('button[data-mode="free"]'); time.sleep(2)
    for nm, x, y in (('Lake Trail', -1420, 290), ('Street E-20', 100, -20)):
        pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b));}''', [nm, x, -y]); time.sleep(3.5)
        print(q, nm, pg.evaluate('JSON.stringify(__game.renderer.info.render)')); shot('h_%d_%s' % (q, nm[:4]))
# fallback path: no decoder
pg.evaluate("localStorage.setItem('aurelia_qual','1')")
pg.add_init_script("Object.defineProperty(window,'MeshoptDecoder',{get(){return undefined},set(v){}})"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=180000)
pg.click('button[data-mode="free"]'); time.sleep(3); print('fallback ok', pg.evaluate('__game.FLO.bt.size'), pg.evaluate('Object.keys(__game.FLO.lib).length')); shot('h_fallback')
