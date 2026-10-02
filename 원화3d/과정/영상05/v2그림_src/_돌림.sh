#!/bin/sh
# 쓰는 법: sh _돌림.sh 8-1 [8-2 ...]  — 블렌더 렌더 + 흰 바탕 마감
cd "$(dirname "$0")"
for n in "$@"; do
  "/c/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b -P "$n.py" 2>&1 | grep -E "Error|Traceback|File \"|^  |Saved" | grep -v "^  *$" | head -20
  python _마감.py "$n"
done
