#!/usr/bin/env bash
# Sketchfab 모델을 헤드리스로 받는다. Blender GUI 애드온이 없어도 된다.
#
#   ./fetch_asset.sh <uid> <이름>
#
# 토큰은 sketchfab.com/settings/password 에서 발급받아 `.sketchfab_token` 에 한 줄로
# 넣어 둔다 (.gitignore 됨). 대화에 붙여넣을 필요 없다.
set -u
cd "$(dirname "$0")"
UID_=${1:?uid}
NAME=${2:?name}
TOK=${SKETCHFAB_TOKEN:-$(cat .sketchfab_token 2>/dev/null)}
[ -n "${TOK:-}" ] || { echo "토큰 없음 -> .sketchfab_token 에 넣어라"; exit 1; }

J=$(curl -s -m 40 -H "Authorization: Token $TOK" \
      "https://api.sketchfab.com/v3/models/$UID_/download")
URL=$(python -c "import json,sys;d=json.load(sys.stdin);print((d.get('gltf') or d.get('glb') or {}).get('url',''))" <<<"$J")
[ -n "$URL" ] || { echo "다운로드 URL 없음. 응답:"; echo "$J" | head -c 400; exit 1; }

mkdir -p "assets/$NAME"
curl -sL -m 300 -o "assets/$NAME.zip" "$URL" || exit 1
python -c "import zipfile,sys;zipfile.ZipFile('assets/$NAME.zip').extractall('assets/$NAME')" || exit 1
echo "받음: assets/$NAME"
find "assets/$NAME" -type f \( -name '*.gltf' -o -name '*.glb' -o -name '*.bin' \) -printf '  %p  %s bytes\n' 2>/dev/null \
  || find "assets/$NAME" -type f | head -20
