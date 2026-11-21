import os
import json
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','1'); localStorage.setItem('aurelia_mob', '" + os.environ.get('MOB','0') + "')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(20)
for name, idx in [('Street N0', 40), ('Ring', 600)]:
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i))}''', [name, idx]); time.sleep(8)
    r = pg.evaluate('''()=>{const g=__game,cam=g.camera;cam.updateMatrixWorld();const T=g.scene.constructor;const F=new (Object.getPrototypeOf(cam).constructor===undefined?null:null);
      const fr=new (window.THREE||window.T3||{}).Frustum ? null:null; return 0}''') if False else None
    r = pg.evaluate('''()=>{const g=__game,cam=g.camera,S={};const M=cam.projectionMatrix.clone().multiply(cam.matrixWorldInverse);
      const fr=new cam.frustum_ctor||null;return 0}''') if False else None
    r = pg.evaluate('''()=>{const g=__game,S={};let tot=0,tt=0;
      g.scene.traverseVisible(o=>{if(!o.isMesh&&!o.isPoints)return;const key=(o.name||'?').slice(0,34);
        const gi=o.geometry; let tr=gi.index?gi.index.count/3:(gi.attributes.position?gi.attributes.position.count/3:0); if(o.isInstancedMesh) tr*=o.count;
        const s=S[key]||(S[key]=[0,0]);s[0]++;s[1]+=tr;tot++;tt+=tr});
      return {tot,tt,top:Object.entries(S).sort((a,b)=>b[1][0]-a[1][0]).slice(0,22),toptri:Object.entries(S).sort((a,b)=>b[1][1]-a[1][1]).slice(0,10)}}''')
    print('==', name, r['tot'], int(r['tt']))
    for k,v in r['top']: print('  n %6d tri %9d  %s'%(v[0],v[1],k))
    print('  -- by triangles')
    for k,v in r['toptri']: print('  n %6d tri %9d  %s'%(v[0],v[1],k))
