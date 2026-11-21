pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(8)
print('BOXSP', pg.evaluate("(()=>{const s={};const seen=new Set();for(const c of __game.obGrid.values())for(const o of c.o){if(!o.sp||seen.has(o))continue;seen.add(o);s[o.sp]=(s[o.sp]||0)+1}return JSON.stringify(s)})()"))
