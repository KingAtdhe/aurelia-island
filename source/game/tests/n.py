pg.click('button[data-mode="free"]'); time.sleep(1.5)
def at(name, i):
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i));}''', [name, i]); time.sleep(2.4)
at('Ring', 395); shot('n_sea'); at('Farm Road', 44); shot('n_shop'); at('Lake Trail', 90); shot('n_forest'); at('Dune Road', 60); shot('n_desert')
pg.click('#bMenu'); time.sleep(.3); pg.click('#oTime'); time.sleep(.3); pg.click('button[data-mode="free"]'); time.sleep(1)
at('Street E-20', 44); shot('n_night_city'); at('Ring', 395); shot('n_night_bridge'); print(st(), pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
