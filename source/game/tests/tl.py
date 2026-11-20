pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
print('RES', pg.evaluate("()=>{const L=__life; const out=[]; for(let k=0;k<60;k++){ for(let i=0;i<20;i++) L.step(0.05); out.push(L.cars.filter(c=>c.r.type==='street'&&c.cur<0.3).length);} return out.join(',')}"))
