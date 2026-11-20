pg.click('button[data-mode="circuit"]'); time.sleep(1); shot('race0')
pg.keyboard.down('ArrowUp'); time.sleep(25)
print('race', pg.evaluate('(()=>{const r=__game.race;return {state:r.state,prog:r.prog,lap:r.lap,t:+r.t.toFixed(1)}})()'), st()); shot('race1')
pg.keyboard.up('ArrowUp')
# water: drive into the bay
pg.evaluate('__game.placeCar({x:-150,y:3.2,z:420,h:0})'); time.sleep(.5); print('quay', st()); pg.keyboard.down('ArrowUp'); time.sleep(9); print('after bay', st()); shot('bay'); pg.keyboard.up('ArrowUp')
# building collision in the city
pg.evaluate('__game.placeCar({x:0,y:14,z:19,h:1.0})'); pg.keyboard.down('ArrowUp'); time.sleep(8); print('city crash', st()); shot('crash'); pg.keyboard.up('ArrowUp')
pg.click('#bMap'); time.sleep(.6); shot('map')
