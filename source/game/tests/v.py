pg.wait_for_function('window.__detail === 1', timeout=180000)
pg.click('button[data-mode="free"]'); time.sleep(2)
W=pg.evaluate("__game.W.landmarks.map(l=>l.name)"); print(W[:50])
def near(name, x, y, tag):
    pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', [name, x, -y]); time.sleep(4); shot(tag)
near('Farm Road', 610, -850, 'v_village'); near('Farm Road', 560, -800, 'v_village2')
