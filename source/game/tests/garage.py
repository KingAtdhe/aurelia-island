import json
errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_tod','0'); localStorage.setItem('aurelia_prog', JSON.stringify({cr: 30000}))"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('#bGarage'); time.sleep(1); shot('g_0')
btns = pg.query_selector_all('#gGrid .item button'); print('BUTTONS', len(btns))
btns[0].click(); time.sleep(0.3)                        # engine stage 1
pg.query_selector_all('#gGrid .paints button')[5].click(); time.sleep(1)    # electric blue
print('PROG', pg.evaluate("localStorage.getItem('aurelia_prog')"), 'VEH', pg.evaluate("[__game.VEH.tq, __game.VEH.mu]"))
shot('g_1'); pg.click('#gClose'); pg.click('button[data-mode="free"]'); time.sleep(8); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')"); shot('g_2')
c0 = pg.evaluate("JSON.parse(localStorage.getItem('aurelia_prog')).cr")
pg.evaluate('''()=>{const g=__game;g.DS.cur=1234;g.DS.bank()}''')
print('CREDIT gain', pg.evaluate("JSON.parse(localStorage.getItem('aurelia_prog')).cr") - c0)
pg.click('#bMenu'); pg.click('#oSteer'); print('STEER', pg.evaluate("document.getElementById('oSteer').textContent"), pg.evaluate("document.getElementById('padL').style.visibility")); pg.click('#oSteer'); pg.click('#oSteer'); print('STEER back', pg.evaluate("document.getElementById('oSteer').textContent"))
print('ERRS', errs)
