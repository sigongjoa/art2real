#!/usr/bin/env bash
# 대본 tsv 한 장 → 세로 쇼츠 mp4 (Remotion 공장). 로컬 에이전트가 이 명령 하나만 돌린다.
# 쓰는 법: bash 원화3d/과정/쇼츠/굽기.sh <대본.tsv> <영문슬러그>
# 내레이션 글이 Microsoft edge-tts 로 나간다. QA 프레임은 만들기만 하고 판정은 사람/Claude.
set -euo pipefail
TSV=$(cd "$(dirname "$1")" && pwd -W)/$(basename "$1"); SLUG=$2
F=/g/claude-faceless-shorts-creator
cd "$F"
LINE=$(python tools/new_short_ko.py "$TSV" "$SLUG" | head -1)          # "short-N-slug · CompName · k scenes"
ID=$(echo "$LINE" | awk '{print $1}'); COMP=$(echo "$LINE" | awk '{print $3}'); N=${ID#short-}; N=${N%%-*}
echo "[1/5] 뼈대 $ID $COMP"
QA=$(python tools/gen_voice_edge.py --beats shorts/$ID/beats.json --voice ko-KR-SunHiNeural \
      --emit-ts remotion/src/shots/short-$N/vo.gen.ts --tsx remotion/src/shots/short-$N/$COMP.tsx | grep "QA frames" | sed 's/.*: //')
echo "[2/5] 목소리 · QA 프레임 $QA"
cd remotion
npm run gen >/dev/null
ERR=$(npx tsc --noEmit -p . | grep "short-$N" || true); [ -z "$ERR" ] || { echo "타입 오류: $ERR"; exit 1; }
echo "[3/5] 타입 확인 OK"
node scripts/frames.mjs "$COMP" "$QA" --scale=0.5 >/dev/null
echo "[4/5] QA 프레임 → remotion/out/qa/$COMP-f*.png"
node scripts/render-all.mjs "$COMP" --scale=1 2>&1 | tail -1
cd ..
ffmpeg -y -loglevel error -i remotion/out/$COMP.mp4 -i shorts/$ID/voice/voice.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k remotion/out/$COMP-voiced.mp4
echo "[5/5] 끝 $F/remotion/out/$COMP-voiced.mp4"
