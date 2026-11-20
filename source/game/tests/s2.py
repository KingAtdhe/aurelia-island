pg.click('button[data-mode="free"]'); time.sleep(1.5); shot('s2_0')
def at(name, i, off=0):
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i));}''', [name, i]); time.sleep(2.0)
at('Canyon Road', 86); pg.keyboard.down('ArrowUp'); time.sleep(3); pg.keyboard.up('ArrowUp'); print('roundabout', st()); shot('s2_rbt')
at('Farm Road', 100); shot('s2_river'); print('river', st())
at('Street E-20', 44); shot('s2_city'); print('city', st())
at('Street N0', 30); shot('s2_city2')
at('Dish Road', 60); shot('s2_desert')
at('Ring', 1150); shot('s2_coast'); print(pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
