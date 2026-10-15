#!/bin/sh
# 평가51나 조각을 차례로(있는 조각은 건너뜀) · 지킴짓기 · 메모리 8 GB · 사용: sh 평가51나_돌림.sh <이름>
cd "/g/art2real/원화3d/실험_20261013/캐드부품"; V="/g/art2real/트레일/trail10_cadrille/venv/Scripts/python.exe"; export ART_MEM_GB=8
for s in $(seq 0 40 711); do
  f=$(printf "G:/art2real/out/설명/캐드부품/학습51나_%s/평가/%04d.json" "$1" $s); [ -f "$f" ] && continue
  "$V" 평가51나.py "$1" $s $((s+40)) 4 2>&1 | grep -v Warn
done
"$V" 평가51나.py "$1" 판정
