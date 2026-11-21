import json, os
pg.evaluate("localStorage.setItem('aurelia_qual','0'); localStorage.setItem('aurelia_mob','1')"); pg.reload(); pg.wait_for_function('window.__game !== undefined', timeout=400000); pg.wait_for_function('window.__detail === 1', timeout=500000)
pg.click('button[data-mode="free"]'); time.sleep(5)
pg.evaluate('''()=>{const g=__game;window.L={};const c=g.car,I=g.inp,DT=1/120;
 L.reset=()=>{for(const k of ['left','right','gas','brake','hand'])I[k]=0;I.ax=undefined;I.gasA=0;I.brakeA=0};
 L.flat=(h,v)=>{L.reset();g.placeCar({x:680,y:g.hAt(680,200),z:200,h});const fx=Math.sin(h),fz=Math.cos(h);c.vx=fx*v;c.vz=fz*v;c.gear=Math.max(0,Math.min(5,Math.floor(v/12)-1));};
 L.step=n=>{for(let i=0;i<n;i++)g.physics(DT)};
 L.st=()=>({kmh:+(c.speed*3.6).toFixed(1),beta:+(c.beta*57.3).toFixed(1),yr:+c.yr.toFixed(2),ay:+(c.ayf/9.81).toFixed(2),ax:+(c.axf/9.81).toFixed(2),gear:c.gear+1,rpm:c.rpm|0,delta:+(c.delta*57.3).toFixed(1),spin:c.spin});
 // road follower with analogue steering
 L.follow=(R)=>{const q=g.roadQuery(c.x,c.z,c.y,{});if(!q.ok)return;const st=Math.max(1,Math.ceil(30/(R.step||5)));const j=(q.i+st)%R.n,p=R.p;let dh=Math.atan2(p[j*3]-c.x,p[j*3+2]-c.z)-c.h;while(dh>Math.PI)dh-=2*Math.PI;while(dh<-Math.PI)dh+=2*Math.PI;I.ax=-Math.max(-1,Math.min(1,dh*2.5-c.yr*0.15));};
}''')
def J(s, a=None): return pg.evaluate(s, a) if a is not None else pg.evaluate(s)
print('TRACE', json.dumps(J('''(()=>{L.flat(0,40/3.6);const g=__game,c=g.car,tr=[];for(let i=0;i<120*6;i++){g.inp.ax=-0.3;const e=40/3.6-c.speed;g.inp.gasA=Math.max(0,Math.min(1,e*0.6+0.25));g.physics(1/120);
 if(i%15==0)tr.push([+(i/120).toFixed(2),+(c.speed*3.6).toFixed(0),+(c.beta*57.3).toFixed(1),+c.yr.toFixed(2),+(c.delta*57.3).toFixed(1),+(c.ar*57.3).toFixed(1),+(c.af*57.3).toFixed(1),+c.thr.toFixed(2),c.drift>0?1:0,c.spin?1:0,c.gear+1])}return tr})()''')))
