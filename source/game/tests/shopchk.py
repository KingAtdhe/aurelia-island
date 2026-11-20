pg.evaluate("localStorage.setItem('aurelia_qual','2')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(25)
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
for k,(x,z,h) in enumerate([(-476,192.3,1.5708),(-452,192.3,-1.5708)]):
    pg.evaluate("([x,z,h])=>{__game.placeCar({x:x,y:14.3,z:z,h:h})}", [x,z,h]); time.sleep(10); shot('sc_%d'%k)
print(pg.evaluate("(()=>{let n=0,v=0;__game.scene.traverse(o=>{if(o.isInstancedMesh&&o.material&&/Shop/.test(o.material.name)){n++; if(o.visible)v++;}});return [n,v]})()"))
