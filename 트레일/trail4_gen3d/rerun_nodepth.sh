#!/bin/sh
# 깊이 보정 없이, 정렬 수정 + 재질 클래스 면단위 + 표면평활만 적용
B="C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
set -e
DF_POSTSMOOTH=12 "$B" -b --python desmooth.py -- out/win_norm.blend out/nd_base 12 2>&1 | grep -E "평활 "
"$B" -b --python project_parts.py -- out/nd_base.blend out/nd_parts.blend 2>&1 | grep -E "광선검사|armor|dark|gold"
SNAP_BAND=8 "$B" -b --python snap_creases.py -- out/nd_parts.blend out/nd_parts2.blend 2>&1 | grep -E "파츠 "
"$B" -b --python assign_named.py -- out/nd_parts2.blend out/nd_named.blend 2>&1 | grep -E "최근접|배정된"
SNAP_BAND=8 "$B" -b --python snap_creases.py -- out/nd_named.blend out/nd_named2.blend 2>&1 | grep -E "파츠 "
UV_PRESMOOTH=10 "$B" -b --python make_uv2.py -- out/nd_named2.blend out/nd_uv.blend 2>&1 | grep -E "섬 합계"
"$B" -b --python repack_atlas.py -- out/nd_uv.blend out/nd_atlas.blend 2>&1 | grep -E "^\[후\]"
"$B" -b --python bake_art.py -- out/nd_atlas.blend out/nd_baked 2>&1 | grep -E "판 배정|래스터화"
"$B" -b --python shot_baked.py -- out/nd_baked.blend out/ndbk 2>&1 | grep -cE "BAKESHOT" > /dev/null
"$B" -b --python shot_side.py -- out/nd_baked.blend out/ndsd 2>&1 | grep -cE "SIDESHOT" > /dev/null
echo DONE
