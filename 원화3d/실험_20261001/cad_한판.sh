#!/usr/bin/env bash
# 한 판: freecadcmd 짓기 → 색 합치기 → 판정 시트 (10-04 피드백 루프 — 판마다 보고 다음을 정한다)
# bash cad_한판.sh <V> <판정 제목>
set -e
V=$1; T=$2; S="C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad"
cp "$(dirname "$0")/cad_짓기N.py" "$S/buildN.py"; echo $V > "$S/ver.txt"
( cd "$S" && timeout 500 "/c/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" buildN.py 2>&1 | tr '\r' '\n' | grep -oE "VER [0-9]+ .*|Error.*|Traceback.*" | head -3 )
cd "/g/art2real/원화3d/out/오메가몬2/블렌더" && python - "$V" <<'PY'
import trimesh, numpy as np, os, sys
v=int(sys.argv[1]); S="C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
col={"helmet":(232,234,244),"visor":(222,226,240),"visor2":(240,242,250),"mask":(214,218,232),"core":(30,30,36),"horn":(236,238,248),"eye":(140,215,250),"socket":(20,20,26),"antenna":(210,175,60),"cheek":(220,224,238),"bolt":(40,110,235),"ridge":(238,240,250),"faceplate":(228,232,244),"nose":(232,236,248),"spike":(226,230,244)}
ms=[]
for nm,c in col.items():
    f=S+f"{nm}_v{v}.stl"
    if os.path.exists(f):
        m=trimesh.load(f); m.visual.vertex_colors=np.tile(list(c)+[255],(len(m.vertices),1)).astype(np.uint8); ms.append(m)
a=trimesh.util.concatenate(ms); trimesh.Trimesh(a.vertices,a.faces,vertex_colors=a.visual.vertex_colors,process=False).export(f"CAD_v{v}.ply",encoding="ascii")
PY
cp "$S/omega_head_v$V.FCStd" "/g/art2real/원화3d/out/오메가몬2/cad/" 2>/dev/null || true
cd "/g/art2real/원화3d/실험_20261001" && python 판정시트.py "CAD_v${V}_판정" "v$((V-1))=CAD_v$((V-1))" "$T=CAD_v$V" | tail -1
