import json
exec(open('tests/lab.py').read().split("def J(")[0])
print('REV', json.dumps(pg.evaluate('''(()=>{L.flat(0,0);const g=__game,c=g.car,tr=[];for(let i=0;i<120*6;i++){if(i<120*4)g.inp.brake=1;else{g.inp.brake=0;g.inp.gas=1}g.physics(1/120);
  if(i%30==0){const f=c.vx*Math.sin(c.h)+c.vz*Math.cos(c.h),l=c.vx*Math.cos(c.h)-c.vz*Math.sin(c.h);tr.push([+(i/120).toFixed(2),+f.toFixed(2),+l.toFixed(2),+c.yr.toFixed(2),+c.h.toFixed(2),c.gear+1,c.rpm|0])}}L.reset();return tr})()''')))
