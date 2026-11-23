set -e
# usage: bash build_car.sh <car>   -> /tmp/<car>_n.glb
C=$1; cd /home/claude/traffic
# PRE = pre-decimation before the zone cuts. 0.25 makes the hatch/saloon/SUV bodies 28-34k tris (was 47-56k at 1.0) with
# clean renders; the boxy van and pickup get ragged taillight/grille edges below 1.0, so they keep the full pass.
case $C in van|pickup) DPRE=1.0;; *) DPRE=0.25;; esac
export PRE=${PRE:-$DPRE} NSIG=${NSIG:-2.0}
LAT=${LAT:-0.085} CAR=$C OUT=/tmp/${C}_body.blend python3 build_body.py -- ${RATIO:-0.03} > /tmp/${C}_b.log 2>&1
CAR=$C OUT=/tmp/$C python3 ${C}_parts.py > /tmp/${C}_p.log 2>&1
CAR=$C python3 patch_normals.py /tmp/$C.glb /tmp/${C}_n.glb
python3 share_tyre_tex.py /tmp/${C}_n.glb /tmp/${C}_n.glb >> /tmp/${C}_p.log   # tyres use the shared tyre_*.png next to the GLB
grep -E "TRIS" /tmp/${C}_p.log
