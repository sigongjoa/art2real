#!/bin/sh
B="C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
for k in 15 40 80 150; do
  echo "=== SMOOTH $k ==="
  DF_SMOOTH=$k "$B" -b --python depth_fit.py -- out/win_norm.blend out/df_s$k.blend 2>&1 | grep -E "깊이 배율"
  "$B" -b --python win_render.py -- out/df_s$k.blend out/dfs$k 2>&1 | grep -cE "WINRENDER" > /dev/null
done
echo DONE
