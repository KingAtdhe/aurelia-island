import json
pg.set_viewport_size({'width': 844, 'height': 390})
pg.evaluate("localStorage.setItem('aurelia_qual','1'); localStorage.setItem('aurelia_mob','1'); localStorage.setItem('aurelia_tod','0')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(6); pg.evaluate("document.querySelectorAll('#toast').forEach(e=>e.style.display='none')")
# drive a scripted handbrake drift on the circuit, stepping physics + effects + scoring at 120 Hz inside the page
SIM = '''(([secs, phase])=>{const g=__game,c=g.car,I=g.inp;window.__nocoll=true;
  if(phase==='start'){const R=g.roads.find(r=>r.name==='Circuit');const p=g.roadPoint(R,g.W.circuit.start+6);g.placeCar(p);c.vx=Math.sin(p.h)*75/3.6;c.vz=Math.cos(p.h)*75/3.6;c.gear=1;}
  for(let i=0;i<secs*120;i++){const t=i/120;
    if(phase==='start'){I.left=t<0.7?1:0;I.hand=t>0.3&&t<0.7?1:0;I.gas=t>0.7?1:0}
    g.physics(1/120);g.FX.update(1/120);g.DS.update(1/120)}
  return {kmh:c.speed*3.6|0,beta:+(c.beta*57.3).toFixed(0),delta:+(c.delta*57.3).toFixed(0),slip:+c.slipR.toFixed(1),cur:g.DS.cur|0,mul:g.DS.mul,total:g.DS.total}})'''
print('S1', pg.evaluate(SIM, [2.2, 'start'])); time.sleep(4); shot('ds1')
print('S2', pg.evaluate(SIM, [1.5, 'hold'])); time.sleep(4); shot('ds2')
pg.evaluate("__game.inp.gas=0;__game.inp.left=0")
print('S3', pg.evaluate(SIM, [3.0, 'hold'])); time.sleep(4); shot('ds3')
