# -*- coding: utf-8 -*-
"""눈 창 파기 E 판 (10-05 원형사 패널 1 순위: 휘지 말고 더하고 빼기 · 카토키 「퍼티 붙여 깎기」)
python 눈창파기.py <입력 판> <출력 판> <배율> <깊이>
  바탕: TripoSG 정리 + 부위 맞춤(F1) — 열린 구멍(지운 조각 자리)은 메워 닫힌 몸으로
  눈 창 윤곽 = 원화 정면에서 잰 왼 창(자료/cad_눈창.json · 축 A 틀) → TripoSG 틀은 x + 22(정렬 틀 원점 = 마스크 가운데 열 121, 축 A = 143)
  오른 창 = 축 A(TripoSG 틀 x = 22) 거울 · 창 가운데 기준 배율 · 앞 겉(창 가운데 광선)에서 깊이만큼 파냄
  창 안 면 = 검정(도색 자리) · 창 바닥에 파란 눈알(반지름 = 창 높이 × 0.32)"""
import sys, json, numpy as np, trimesh
from shapely.geometry import Polygon
from matplotlib.path import Path
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"
src, dst, SC, DP = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
m = trimesh.load(B + src + ".ply", process=False); m = trimesh.Trimesh(m.vertices, m.faces, process=True)
print("닫힘", m.is_watertight, m.is_volume)
W = np.array(json.load(open("G:/art2real/원화3d/실험_20261001/자료/cad_눈창.json", encoding="utf-8"))["왼"]); W[:, 0] += 22.0
AX = 22.0
wins = [W, np.c_[2 * AX - W[:, 0], W[:, 1]][::-1]]
import os
if os.environ.get("AT_TRIPO"):   # E2: 원화 좌표에 파니 TripoSG 자기 차양보다 20 아래(볼 높이)에 파였다 — 실루엣은 맞아도 속 배치가 다름 → 창 모양은 원화 · 자리는 TripoSG 눈 부위(3) 가운데
    lab = np.load("G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/트리포_T6_라벨20.npy"); T6 = trimesh.load(B + "트리포_T6.ply", process=False)
    ec = m.vertices[np.unique(T6.faces[lab == 3])].mean(0) if len(m.vertices) == len(T6.vertices) else None
    rc = np.array([ec[0], ec[2]]); W2 = W - W.mean(0) + rc
    wins = [np.c_[2 * AX - W2[:, 0], W2[:, 1]][::-1], W2]; print("눈 부위 가운데", rc.round(1))
eyes = []; prisms = []
for P in wins:
    c = P.mean(0); P = (P - c) * SC + c
    hit = m.ray.intersects_location([[c[0], -800, c[1]]], [[0, 1, 0]], multiple_hits=False)[0]
    yf = hit[0, 1] if len(hit) else -60.0
    pr = trimesh.creation.extrude_polygon(Polygon(P).buffer(0), 800 + yf + DP)   # 다각형(x, z) → 돌려 y 로 밀기
    pr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); pr.apply_translation([0, -800 - 0 + (800 + yf + DP), 0])
    pr.vertices[:, 1] = np.where(pr.vertices[:, 1] > yf + DP - 1e-6, yf + DP, -800.0)   # 앞(−800) ~ 바닥(yf + 깊이)
    prisms.append((Path(P), yf, DP))
    h = P[:, 1].max() - P[:, 1].min(); r_ = 0.24 * h; e = trimesh.creation.icosphere(3, radius=r_); e.apply_translation([c[0], yf + DP - 0.5 * r_, c[1]]); eyes.append(e)   # 눈알 앞이 겉보다 뒤(창 안)
    m = trimesh.boolean.difference([m, pr], engine="manifold")
print("파낸 뒤 닫힘", m.is_watertight, len(m.faces))
fc = np.tile([228, 232, 240, 255], (len(m.faces), 1)); cen = m.triangles_center
for pth, yf, dp in prisms:
    inn = pth.contains_points(cen[:, [0, 2]], radius=0.5) & (cen[:, 1] > yf - 2)
    fc[inn] = [20, 20, 26, 255]
mm = trimesh.Trimesh(m.vertices, m.faces, face_colors=fc, process=False)
ec = [trimesh.Trimesh(e.vertices, e.faces, face_colors=np.tile([140, 215, 250, 255], (len(e.faces), 1)), process=False) for e in eyes]
out = trimesh.util.concatenate([mm] + ec)
vc = np.zeros((len(out.vertices), 4), np.uint8)
for f, c_ in zip(out.faces, out.visual.face_colors): vc[f] = c_
trimesh.Trimesh(out.vertices, out.faces, vertex_colors=vc, process=False).export(B + dst + ".ply", encoding="ascii"); print(dst, "배율", SC, "깊이", DP)
