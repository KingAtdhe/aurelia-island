pg.wait_for_function('window.__detail === 1', timeout=180000)
pg.click('button[data-mode="free"]'); time.sleep(2)
pg.evaluate('''([n,x,z])=>{const R=__game.roads.find(r=>r.name===n);let b=0,bd=1e9;for(let i=0;i<R.n;i++){const p=__game.roadPoint(R,i),d=Math.hypot(p.x-x,p.z-z);if(d<bd){bd=d;b=i}}__game.placeCar(__game.roadPoint(R,b))}''', ['Street E-20', 300, 20]); time.sleep(4); shot('k_city3')
