set -e
# usage: bash mk.sh <car> [views]  -> /tmp/<car>_n.glb and renders in the scratchpad
C=$1; cd /home/claude/traffic; S=/tmp/claude-0/-home-claude-aurelia-island/3ff9d284-daa9-5a9b-ae7d-a94693848491/scratchpad
case $C in porto) DPRE=1.0;; *) DPRE=0.25;; esac
PRE=${PRE:-$DPRE} NSIG=2.0 LAT=0.085 CAR=$C OUT=/tmp/${C}_body.blend python3 build_body.py -- ${RATIO:-0.03} > /tmp/${C}_b.log 2>&1
CAR=$C OUT=/tmp/$C python3 ${C}_parts.py > /tmp/${C}_p.log 2>&1 || { grep -A5 Traceback /tmp/${C}_p.log; exit 1; }
NSIG=2.0 CAR=$C python3 patch_normals.py /tmp/$C.glb /tmp/${C}_n.glb > /dev/null
python3 share_tyre_tex.py /tmp/${C}_n.glb /tmp/${C}_n.glb >> /tmp/${C}_p.log
grep TRIS /tmp/${C}_p.log
V=${2:-q,side,front,rear,qr,qn}
timeout 400 python3 look.py /tmp/${C}_n.glb $S/$C $V > /dev/null 2>&1; python3 $S/sheet.py $S/$C $V
