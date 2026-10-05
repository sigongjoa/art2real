# -*- coding: utf-8 -*-
"""얼굴 교체 G 판 (10-05 · 사용자 「정답을 최대한 참고」 → FRA 머리 부품: 투구 좌우 껍데기 + 가운데 작은 얼굴 부품(눈 블록 · V 코 · 턱)이 투구 구멍 뒤에 끼워짐)
python 얼굴교체.py <출력 판> [얼굴 배율=1.0]
  바탕: 부위맞춤_F1닫힘(TripoSG) · 그래프 부위 중 눈 · 얼굴 · 아래 얼굴 · 매달린 조각을 지움 → 투구 껍데기(돔 · 차양 · 뿔 · 안테나 · 볼 · 옆)만 남김
  얼굴 부품 = CAD v57 의 얼굴판 · 눈구멍 · 눈 · 부리(원화 치수) → TripoSG 틀로 옮김(x + 22) · 눈 가운데를 TripoSG 눈 부위 가운데에 맞춤(y · z 이동)"""
import sys, json, numpy as np, trimesh
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; O = "G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/"
SC = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
dst = sys.argv[1]; FS = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
m = trimesh.load(B + "부위맞춤_F1닫힘.ply", process=False); lab = np.load(O + "트리포_T6_라벨20.npy")
G = json.load(open(O + "트리포_T6_그래프20.json", encoding="utf-8")); nm = {d["id"]: d["이름(눈)"] for d in G["노드"]}
지울 = [i for i, s in nm.items() if any(k in s for k in ("눈", "얼굴", "지움"))]
print("지움", [nm[i] for i in 지울])
eye_c = m.vertices[np.unique(m.faces[lab == 3])].mean(0)
shell = trimesh.Trimesh(m.vertices, m.faces[~np.isin(lab, 지울)], process=True)
col = {"faceplate": (228, 232, 244), "socket": (20, 20, 26), "eye": (140, 215, 250), "mask": (214, 218, 232), "nose": (232, 236, 248)}
parts = {}
for k in col:
    try: parts[k] = trimesh.load(SC + f"{k}_v57.stl")
    except Exception: pass
ce = parts["eye"].vertices.mean(0)   # CAD 눈 둘의 가운데(x ≈ 0)
# 오른 눈(+x) 위치를 TripoSG 눈 부위(3) 가운데로: x 는 축 이동 +22 · y · z 는 눈 가운데 맞춤
ev = parts["eye"].vertices; right = ev[ev[:, 0] > 0].mean(0)
T = np.array([22.0, 0, 0]); T[1:] = eye_c[1:] - right[1:] * FS
ms = [trimesh.Trimesh(shell.vertices, shell.faces, vertex_colors=np.tile([232, 234, 244, 255], (len(shell.vertices), 1)).astype(np.uint8), process=False)]
for k, p in parts.items():
    v = p.vertices * FS + T; ms.append(trimesh.Trimesh(v, p.faces, vertex_colors=np.tile(list(col[k]) + [255], (len(v), 1)).astype(np.uint8), process=False))
out = trimesh.util.concatenate(ms); out.export(B + dst + ".ply", encoding="ascii")
print(dst, "눈 TripoSG", eye_c.round(1), "CAD 오른 눈", right.round(1), "이동", T.round(1))
