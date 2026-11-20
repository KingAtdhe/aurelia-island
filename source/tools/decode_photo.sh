#!/bin/bash
# decode the CC0 KTX2 textures to raw RGBA in blender/photo
SRC=/home/claude/papyszoo/cc0-public-domain-textures/packs/ambientcg-textures/textures
OUT=/home/claude/aurelia_in/aurelia-handoff/blender/photo; mkdir -p $OUT
for f in $SRC/*/*.ktx2; do
  b=$(basename $f .ktx2); n=${b%%_1K-PNG_*}; k=${b##*_1K-PNG_}
  d=$(mktemp -d); (cd $d && /home/claude/basis_universal/bin/basisu -unpack $f -no_ktx >/dev/null 2>&1)
  p=$(ls $d/*_rgba_RGBA32_level_0_*.png | head -1)
  python3 -c "from PIL import Image;import numpy as np;a=np.asarray(Image.open('$p').convert('RGBA'));a.tofile('$OUT/${n}_${k}.raw')"
  rm -rf $d
done
ls $OUT | wc -l
