pg.click('button[data-mode="free"]'); time.sleep(1)
names = pg.evaluate('__game.W.regions.map(r=>r.name)')
for i, nm in enumerate(names):
    pg.evaluate('''(i)=>{const r=__game.W.regions[i];let b=null,bd=1e12;__game.roads.forEach(R=>{for(let k=2;k<R.n-2;k+=2){const d=(R.p[k*3]-r.x)**2+(R.p[k*3+2]-r.z)**2;if(d<bd){bd=d;b=__game.roadPoint(R,k);}}});__game.placeCar(b);}''', i)
    time.sleep(1.2); pg.keyboard.down('ArrowUp'); time.sleep(2.5); pg.keyboard.up('ArrowUp'); print(nm, st()); shot('tour%d' % i)
# tunnel and mountain viaduct
t = pg.evaluate('__game.W.tunnels'); print('tunnels', t)
for k, (ri, a, ln) in enumerate(t[:2]):
    pg.evaluate('([ri,i])=>__game.placeCar(__game.roadPoint(__game.roads[ri],i))', [ri, a - 14]); time.sleep(1.5); shot('tunA%d' % k)
    pg.evaluate('([ri,i])=>__game.placeCar(__game.roadPoint(__game.roads[ri],i))', [ri, a + ln // 2]); time.sleep(1.5); shot('tunB%d' % k); print('in tunnel', st())
