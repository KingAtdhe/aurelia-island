pg.wait_for_function('window.__detail === 1', timeout=180000)
pg.click('button[data-mode="free"]'); time.sleep(2)
print('props in lib', pg.evaluate("Object.keys(__game.FLO.lib).filter(k=>k.startsWith('prop_')).length"))
def near(name, x, y, tag, cam=None):
    pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', [name, x, -y]); time.sleep(4); shot(tag)
    print(tag, pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
near('Street E-20', 100, -20, 'k_city'); near('Street E-20', 300, -20, 'k_city2'); near('Farm Road', 625, -855, 'k_farm'); near('Ring', -1640, -520, 'k_ring')
