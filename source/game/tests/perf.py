import os, json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','1'); localStorage.setItem('aurelia_mob', '" + os.environ.get('MOB','0') + "')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
for name, idx in [('Ring', 600), ('Street N0', 40), ('Summit Pass', 60), ('Harbour Bridge', 100)]:
    try:
        pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i))}''', [name, idx]); time.sleep(8)
        r = pg.evaluate('''async()=>{const i=__game.renderer.info;i.autoReset=false;i.reset();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const calls=i.render.calls,tris=i.render.triangles;i.autoReset=true;return {calls:calls/2,tris:tris/2,geo:i.memory.geometries,tex:i.memory.textures,prog:i.programs.length, pr:__game.renderer.getPixelRatio(), vis:(()=>{let n=0;__game.scene.traverseVisible(o=>{if(o.isMesh)n++});return n})()}}''')
        print(name, json.dumps(r))
    except Exception as e: print(name, 'ERR', e)
