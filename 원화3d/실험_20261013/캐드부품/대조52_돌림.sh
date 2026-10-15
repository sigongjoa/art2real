#!/bin/sh
# 판정기준51 대조군 다시(다각섬4) · 조각 120 · 일꾼 2 · 메모리 6 GB(인터프리터 상한)
cd "/g/art2real/원화3d/실험_20261013/캐드부품"; V="/g/art2real/트레일/trail10_cadrille/venv/Scripts/python.exe"; export ART_MEM_GB=6
for s in $(seq 0 120 711); do
  f=$(printf "G:/art2real/out/설명/캐드부품/평가52대조/%04d.json" $s); [ -f "$f" ] && continue
  "$V" 평가52대조.py $s $((s+120)) 2>&1 | grep -v Warn
done
"$V" 평가52대조.py 판정
