set -e
# usage: bash build_car.sh <car>   -> /tmp/<car>_n.glb
C=$1; cd /home/claude/traffic
LAT=${LAT:-0.085} CAR=$C OUT=/tmp/${C}_body.blend python3 build_body.py -- ${RATIO:-0.09} > /tmp/${C}_b.log 2>&1
CAR=$C OUT=/tmp/$C python3 ${C}_parts.py > /tmp/${C}_p.log 2>&1
CAR=$C python3 patch_normals.py /tmp/$C.glb /tmp/${C}_n.glb
grep -E "TRIS" /tmp/${C}_p.log
