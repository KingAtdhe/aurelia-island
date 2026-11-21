import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_cam','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(15)
pg.evaluate("document.querySelectorAll('#help,#toast').forEach(e=>e.style.display='none')")
J = '''([pts])=>{const T=window.THREE,g=__game,rc=new T.Raycaster();const out=[];
  for(const [x,y] of pts){rc.setFromCamera(new T.Vector2(x,y),g.camera);rc.far=5000;const hs=rc.intersectObjects(g.scene.children,true).filter(h=>h.object.visible!==false).slice(0,4);
    out.push(hs.map(h=>{let o=h.object,path=[];while(o&&path.length<4){path.push(o.name||o.type);o=o.parent}return {d:+h.distance.toFixed(1),path:path.join('<'),mat:(Array.isArray(h.object.material)?'multi':h.object.material.name),tr:h.object.material.transparent,op:h.object.material.opacity}}))}
  return out}'''
for nm, i, pts, tag in [('Circuit', None, [[-0.06, 0.59], [0.3, 0.7]], 'circ'), ('Eagle Descent', None, [[-0.26, 0.79], [0.52, 0.18], [0.6, 0.3]], 'eagle'), ('Serpentine', None, [[0.16, 0.93], [0.5, 0.9]], 'serp'), ('Peninsula Road', None, [[-0.6, 0.8]], 'pen')]:
    pg.evaluate('''([n])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,Math.floor(R.n*0.35)))}''', [nm]); time.sleep(5)
    pg.evaluate("__game.inp.gas=1"); time.sleep(4); pg.evaluate("__game.inp.gas=0"); time.sleep(1)
    pg.evaluate("__game.inp.brake=1"); time.sleep(3); pg.evaluate("__game.inp.brake=0")
    shot('pk_' + tag)
    print('PICK', tag, json.dumps(pg.evaluate(J, [pts])))
