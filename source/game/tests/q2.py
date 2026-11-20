pg.click('#oQual'); time.sleep(.3); print(pg.inner_text('#oQual'))
pg.click('button[data-mode="free"]'); time.sleep(1.5)
def at(name, i):
    pg.evaluate('''([n,i])=>{const R=__game.roads.find(r=>r.name===n);__game.placeCar(__game.roadPoint(R,i));}''', [name, i]); time.sleep(2.5)
at('Lake Trail', 70); shot('q_forest'); at('Street E-20', 44); shot('q_city'); at('Farm Road', 60); shot('q_country'); at('West Avenue', 120); shot('q_west'); print(st())
