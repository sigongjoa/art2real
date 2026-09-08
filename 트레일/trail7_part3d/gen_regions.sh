#!/usr/bin/env bash
# 부위마다 PartCrafter 를 1024² 로 돌린다. 이미 있는 건 건너뛴다.
set -u
cd "$(dirname "$0")"
for spec in head:4 torso:4 armL:5 armR:4 legs:4; do
  n=${spec%%:*}; p=${spec##*:}
  [ -f "out/rg_$n.glb" ] && { echo "== $n 이미 있음"; continue; }
  echo "== $n (파트 $p)"
  venv/Scripts/python.exe -u run_partcrafter.py "in/omega_$n.png" "out/rg_$n" --parts "$p" \
      > "out/rg_$n.log" 2>&1 || echo "  실패 — out/rg_$n.log"
  grep -a "면 합" "out/rg_$n.log" | tail -1
done
echo "== 전부 끝"
