pg.evaluate("localStorage.setItem('aurelia_qual','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(3)
print('RES', pg.evaluate("()=>{const L=__life; let ov=0,frames=0; for(let i=0;i<2400;i++){ L.step(0.05); if(i%10) continue; frames++; for(let a=0;a<L.cars.length;a++) for(let b=a+1;b<L.cars.length;b++){const A=L.cars[a],B=L.cars[b]; if(Math.hypot(A.sx-B.sx,A.sz-B.sz)<3) ov++;} } return [ov, frames]}"))
