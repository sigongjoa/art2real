#!/bin/sh
# 천장51 조각을 차례로(이미 있는 조각은 건너뜀) · 메모리 상한 8 GB
cd "/g/art2real/원화3d/실험_20261013/캐드부품"; V="/g/art2real/트레일/trail10_cadrille/venv/Scripts/python.exe"
for s in $(seq 0 40 711); do
  f=$(printf "G:/art2real/out/설명/캐드부품/천장51/%04d.json" $s); [ -f "$f" ] && continue
  "$V" "G:/art2real/트레일/trail10_cadrille/runs/기능0/상한.py" 8 "$V" 천장51.py $s $((s+40)) 4 2>&1 | grep -v Warn
done
"$V" 천장51.py 판정
