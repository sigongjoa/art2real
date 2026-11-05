#!/usr/bin/env bash
# 곡선 점 하나를 기다렸다 끝남 — 11-05 사용자 「점 마다 보여줘야지 또 은근슬쩍 해놓고 안되게 만들라고」
# 사용: bash 하네스/곡선감시.sh <판 로그> <이미 본 점 수>   (Bash run_in_background 로 띄움 → 끝나면 알림 → 곡선.png 보내고 n+1 로 다시 띄움)
# 끝나는 경우(전부 한 줄 출력): 새 곡선 점 · 판 끝(「판 코드」 줄) · 오류(Traceback · MemoryError · CUDA error · Killed) · 로그가 STALL 초(기본 1200) 안 바뀜
# 변수 이름은 영문(bash 는 한글 변수 이름을 못 씀)
LOG="$1"; SEEN="${2:-0}"; STALL="${STALL:-1200}"; N=0
while true; do
  if [ -f "$LOG" ]; then
    TXT=$(tr '\r' '\n' < "$LOG")
    N=$(grep -c '^곡선 {' <<< "$TXT")
    if [ "$N" -gt "$SEEN" ]; then echo "점 $N: $(grep '^곡선 {' <<< "$TXT" | tail -1 | cut -c1-300)"; exit 0; fi
    if grep -qE '^판 코드|^판정 \{' <<< "$TXT"; then echo "판 끝 · 점 $N 개"; exit 0; fi
    ERR=$(grep -E 'Traceback|MemoryError|CUDA error|Killed' <<< "$TXT" | tail -1)
    if [ -n "$ERR" ]; then echo "오류: $(cut -c1-300 <<< "$ERR") · 점 $N 개"; exit 1; fi
    AGE=$(( $(date +%s) - $(stat -c %Y "$LOG") ))
    if [ "$AGE" -gt "$STALL" ]; then echo "로그 멈춤 ${AGE} 초(죽었을 수 있음) · 점 $N 개"; exit 1; fi
  fi
  sleep 20
done
