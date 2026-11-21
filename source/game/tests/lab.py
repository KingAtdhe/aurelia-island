import json, os
pg.evaluate("localStorage.setItem('aurelia_qual','0'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(5)
pg.evaluate('''()=>{const g=__game;window.L={};const c=g.car,I=g.inp,DT=1/120;
 window.__nocoll=true;L.reset=()=>{for(const k of ['left','right','gas','brake','hand'])I[k]=0;I.ax=undefined;I.gasA=0;I.brakeA=0};
 L.flat=(h,v)=>{L.reset();g.placeCar({x:680,y:g.hAt(680,200),z:200,h});const fx=Math.sin(h),fz=Math.cos(h);c.vx=fx*v;c.vz=fz*v;c.gear=Math.max(0,Math.min(5,Math.floor(v/12)-1));};
 L.step=n=>{for(let i=0;i<n;i++)g.physics(DT)};
 L.st=()=>({kmh:+(c.speed*3.6).toFixed(1),beta:+(c.beta*57.3).toFixed(1),yr:+c.yr.toFixed(2),ay:+(c.ayf/9.81).toFixed(2),ax:+(c.axf/9.81).toFixed(2),gear:c.gear+1,rpm:c.rpm|0,delta:+(c.delta*57.3).toFixed(1),spin:c.spin});
 // road follower with analogue steering
 L.follow=(R)=>{const q=g.roadQuery(c.x,c.z,c.y,{});if(!q.ok)return;const st=Math.max(1,Math.ceil(30/(R.step||5)));const j=(q.i+st)%R.n,p=R.p;let dh=Math.atan2(p[j*3]-c.x,p[j*3+2]-c.z)-c.h;while(dh>Math.PI)dh-=2*Math.PI;while(dh<-Math.PI)dh+=2*Math.PI;I.ax=-Math.max(-1,Math.min(1,dh*2.5-c.yr*0.15));};
}''')
def J(s, a=None): return pg.evaluate(s, a) if a is not None else pg.evaluate(s)
out = {}
# 1. acceleration on the ring highway
out['accel'] = J('''(()=>{const g=__game,c=g.car,R=g.roads.find(r=>r.name==='Ring');L.reset();g.placeCar(g.roadPoint(R,388));let t=0,t100=null,t200=null,shifts=[],lg=c.gear;
  for(let i=0;i<120*40;i++){L.follow(R);g.inp.gas=1;g.physics(1/120);t+=1/120;const k=c.speed*3.6;if(t100===null&&k>=100)t100=t;if(t200===null&&k>=200)t200=t;if(c.gear!==lg){shifts.push([+t.toFixed(2),c.gear+1,k|0]);lg=c.gear}}
  return {t100:t100&&+t100.toFixed(2),t200:t200&&+t200.toFixed(2),v40s:(c.speed*3.6)|0,shifts}})()''')
# 2. braking 100-0
out['brake'] = J('''(()=>{const g=__game,c=g.car,R=g.roads.find(r=>r.name==='Ring');L.reset();const p=g.roadPoint(R,388);g.placeCar(p);c.vx=Math.sin(p.h)*27.78;c.vz=Math.cos(p.h)*27.78;c.gear=2;
  const x0=c.x,z0=c.z;let t=0;for(let i=0;i<120*10&&c.speed>0.1;i++){L.follow(R);g.inp.brake=1;g.physics(1/120);t+=1/120}return {dist:+Math.hypot(c.x-x0,c.z-z0).toFixed(1),t:+t.toFixed(2)}})()''')
# 3. skidpad: hold a steering input and a speed
sk = []
for kmh in (40, 70, 100):
    for s in (0.3, 0.6, 1.0):
        sk.append(J('''(([kmh,s])=>{L.flat(0,kmh/3.6);const g=__game,c=g.car;let mb=0,spun=false;for(let i=0;i<120*6;i++){g.inp.ax=-s;const e=kmh/3.6-c.speed;g.inp.gasA=Math.max(0,Math.min(1,e*0.6+0.25));g.inp.gas=0;g.inp.brakeA=e<-2?0.3:0;g.physics(1/120);mb=Math.max(mb,Math.abs(c.beta));if(Math.abs(c.beta)>1.2)spun=true}
          return Object.assign({kmh,s,maxBeta:+(mb*57.3).toFixed(1),spun},L.st())})''', [kmh, s]))
out['skidpad'] = sk
# 4. step steer at 130 km/h, 2 s, lift
out['step'] = J('''(()=>{L.flat(0,130/3.6);const g=__game,c=g.car;let mb=0,myr=0;const tr=[];for(let i=0;i<120*3;i++){g.inp.ax=i<240?-1:0;g.physics(1/120);mb=Math.max(mb,Math.abs(c.beta));myr=Math.max(myr,Math.abs(c.yr));if(i%30==0)tr.push(L.st())}return {maxBeta:+(mb*57.3).toFixed(1),maxYr:+myr.toFixed(2),end:L.st(),tr}})()''')
print('LAB', json.dumps(out, indent=0))
