pg.click('button[data-mode="free"]'); time.sleep(1.5)
def at(name, i):
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i));}''', [name, i]); time.sleep(2.2)
at('Lake Trail', 70); shot('q_forest'); at('Farm Road', 60); shot('q_country'); at('Street E-20', 44); shot('q_city'); at('Ring', 395); shot('q_bridge')
at('Skyline Road', 100); shot('q_mtn'); at('Ring', 1150); shot('q_coast'); print(st(), pg.evaluate('JSON.stringify(__game.renderer.info.render)'))
