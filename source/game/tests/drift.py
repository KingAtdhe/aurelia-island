import json
exec(open('tests/lab.py').read().split("def J(")[0])
def J(s, a=None): return pg.evaluate(s, a) if a is not None else pg.evaluate(s)
SC = '''(([name,kmh,assist])=>{const g=__game,c=g.car,I=g.inp;g.setAssist(assist);L.flat(0,kmh/3.6);c.gear=1;const tr=[];let t=0,maxYr=0,spun=false,phase='';
 const S=(f,dur)=>{for(let i=0;i<dur*120;i++){f(t);g.physics(1/120);t+=1/120;maxYr=Math.max(maxYr,Math.abs(c.yr));if(Math.abs(c.beta)>1.45)spun=true;if(Math.round(t*120)%12==0)tr.push([+t.toFixed(1),phase,c.speed*3.6|0,+(c.beta*57.3).toFixed(0),+c.yr.toFixed(2),+(c.delta*57.3).toFixed(0),c.gear+1])}};
 const keep=(dir,target)=>tt=>{I.gas=1;const b=c.beta*57.3*dir;   // simple player: steer into the turn while the angle is small, let the assist counter-steer
   I.left=0;I.right=0;if(-b<target*0.7&&c.yr*dir<1.3){if(dir>0)I.left=1;else I.right=1}};
 if(name==='hand'){phase='entry';S(()=>{I.left=1;I.gas=0},0.35);phase='hb';S(()=>{I.left=1;I.hand=1},0.4);I.hand=0;phase='hold';S(keep(1,30),4);L.reset();phase='release';S(()=>{},3)}
 if(name==='trans'){phase='entry';S(()=>{I.left=1},0.3);phase='hb';S(()=>{I.left=1;I.hand=1},0.4);I.hand=0;phase='holdL';S(keep(1,30),2.2);L.reset();phase='flick';S(()=>{I.gas=0;I.right=1},0.45);phase='holdR';S(keep(-1,30),2.5);L.reset();phase='release';S(()=>{},3)}
 if(name==='gasonly'){phase='entry';S(()=>{I.left=1},0.35);phase='hb';S(()=>{I.left=1;I.hand=1},0.4);I.hand=0;phase='gas';S(()=>{I.gas=1;I.left=0;I.right=0},4);L.reset();phase='release';S(()=>{},3)}
 if(name==='power'){c.gear=1;phase='power';S(()=>{I.left=1;I.gas=1},3);L.reset();phase='release';S(()=>{},3)}
 if(name==='lift'){phase='corner';S(()=>{I.left=1;I.gas=1},1.5);phase='lift';S(()=>{I.left=1;I.gas=0},1.5);L.reset();phase='end';S(()=>{},2)}
 L.reset();g.setAssist(true);return {name,kmh,assist,maxYr:+maxYr.toFixed(2),spun,tr}})'''
for args in [['gasonly', 70, True], ['hand', 70, True], ['hand', 70, False], ['trans', 75, True], ['power', 45, True], ['lift', 110, True]]:
    r = J(SC, args)
    print('DRIFT', json.dumps({k: r[k] for k in ('name', 'kmh', 'assist', 'maxYr', 'spun')}))
    print('  ' + ' | '.join('%s %s %d %d %.2f %d' % (x[0], x[1], x[2], x[3], x[4], x[5]) for x in r['tr'][::3]))
