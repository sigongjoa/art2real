# -*- coding: utf-8 -*-
"""Pomettini 머리를 바탕으로 (10-05 · 「고쳐」 — 규칙 「있는 3D 부터」 · 사람 판 비교 다섯 규칙)
python 포메바탕.py <판 이름> [단계]
  P1 정렬: 목 기둥(z < −56) 자르고 뿔 끝 → 원화 뿔 끝(z −2) · 턱(z −56) → 원화 턱 끝(z −298) 로 배율 · 축 A(x 0)
         · 앞(얼굴 앞 y −50) → v62 얼굴 앞 깊이(−100) — CAD v62 와 같은 틀(x = 화소 − 143 · z = −행)
  P2 눈 창: 원화에서 잰 눈 창(자료/cad_눈창.json · 같은 틀)을 차양 밑에 판다(닫힌 솔리드라 파기가 된다) · 검은 벽 · 파란 눈알(창 안)"""
import sys, os, json, numpy as np, trimesh
from shapely.geometry import Polygon
from matplotlib.path import Path
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"
nm = sys.argv[1]; ST = int(sys.argv[2]) if len(sys.argv) > 2 else 1
P = trimesh.load(B + "포메원본.ply", process=False); P = trimesh.Trimesh(P.vertices, P.faces, process=True)
P = P.slice_plane([0, 0, -56.0], [0, 0, 1], cap=True)
# P1b: 뿔 끝 · 턱으로 맞추니 몸통이 작아짐(사람 판은 뿔을 과장해 길다) → 몸통끼리: 몸통 위(z 3 · 뿔 뺀 열기) → 투구 꼭대기 −117 · 턱(−56) → −298 · 몸통 가운데 x 5.4 → 0
s = (298 - 117) / (3 - (-56)); v = P.vertices.copy()
v[:, 2] = (v[:, 2] - 3) * s - 117; v[:, 0] = (v[:, 0] - 5.4) * s; v[:, 1] = (v[:, 1] + 50) * s - 100
if ST >= 3:   # P3: 원화 비율 — 사람 판은 뿔 · 안테나를 과장(뿔 끝 z +104 · 원화 −2) → 뿔: 밑동(z −117) 기준 높이 줄여 끝 −2 · 폭 1.8 배 / 안테나: 뿌리 쪽으로 0.6 배
    hz = v[:, 2] > -110; horn = hz & (np.abs(v[:, 0]) < 45)
    bz = -117.0; top = v[horn, 2].max(); k = (-2 - bz) / (top - bz)
    v[horn, 2] = bz + (v[horn, 2] - bz) * k; v[horn, 1] = v[horn, 1]; v[horn, 0] *= float(os.environ.get("HORNW", "1.8"))
    ant = (np.abs(v[:, 0]) > 80) & (v[:, 2] > -230)
    for sg in (1, -1):
        a = ant & (np.sign(v[:, 0]) == sg)
        if a.any():
            root = np.array([sg * 80.0, np.median(v[a, 1]), v[a, 2].min()]); v[a] = root + (v[a] - root) * float(os.environ.get("ANT", "0.6"))
m = trimesh.Trimesh(v, P.faces, process=True); print("P1", len(m.faces), "닫힘", m.is_watertight, m.bounds.round(0).tolist())
fc = np.tile([228, 232, 240, 255], (len(m.faces), 1)); extra = []
if ST >= 2:
    W = np.array(json.load(open("G:/art2real/원화3d/실험_20261001/자료/cad_눈창.json", encoding="utf-8"))["왼"])
    DP = float(os.environ.get("DEPTH", "18")); prisms = []
    for Q in (W, np.c_[-W[:, 0], W[:, 1]][::-1]):
        c = Q.mean(0); Q = (Q - c) * float(os.environ.get("EYESC", "1.0")) + c   # P5: 원화 정면은 눈 창 하나가 머리 폭의 약 1/4
        hit = m.ray.intersects_location([[c[0], -800, c[1]]], [[0, 1, 0]], multiple_hits=False)[0]
        yf = hit[0, 1] if len(hit) else -80.0
        pr = trimesh.creation.extrude_polygon(Polygon(Q).buffer(0), 1.0); pr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        pv = pr.vertices; pv[:, 1] = np.where(pv[:, 1] > pv[:, 1].mean(), yf + DP, -800.0); pr = trimesh.Trimesh(pv, pr.faces, process=True); trimesh.repair.fix_normals(pr)
        m = trimesh.boolean.difference([m, pr], engine="manifold"); prisms.append((Path(Q), yf))
        h = np.ptp(Q[:, 1]); r = min(0.3 * h, 0.45 * DP); e = trimesh.creation.icosphere(3, radius=r); e.apply_translation([c[0], yf + DP - 0.3 * r, c[1]]); extra.append(e)
    fc = np.tile([228, 232, 240, 255], (len(m.faces), 1)); cen = m.triangles_center
    for pth, yf in prisms: fc[pth.contains_points(cen[:, [0, 2]], radius=0.5) & (cen[:, 1] > yf - 1) & (cen[:, 1] < yf + DP + 1)] = [20, 20, 26, 255]
    print("P2 눈 창 깊이", DP, "닫힘", m.is_watertight)
if ST >= 4:   # P4: 뿔 → 코판 — 원화는 뿔 밑동이 눈 사이로 내려와 V 능선(코판)이 된다 · P3 는 뿔이 돔 위 막대로 끝남
    hb = m.vertices[(m.vertices[:, 2] > -125) & (m.vertices[:, 2] < -105) & (np.abs(m.vertices[:, 0]) < 40)]
    w = np.ptp(hb[:, 0]) / 2 if len(hb) else 18.0; zt, zb = -112.0, float(os.environ.get("KEELZ", "-212"))
    def fy(x, z):
        h = m.ray.intersects_location([[x, -800, z]], [[0, 1, 0]], multiple_hits=False)[0]; return h[0, 1] if len(h) else -80.0
    yt, yb = fy(0, zt), fy(0, zb); ridge = float(os.environ.get("RIDGE", "10"))
    pts = [[-w, yt + 2, zt], [w, yt + 2, zt], [0, yt - ridge, zt], [0, yb - ridge * 0.6, zb], [-3, yb + 2, zb + 4], [3, yb + 2, zb + 4],
           [-w, yt + 30, zt], [w, yt + 30, zt], [0, yb + 25, zb]]
    keel = trimesh.convex.convex_hull(np.array(pts)); m = trimesh.boolean.union([m, keel], engine="manifold"); print("P4 코판 폭", round(2 * w, 1), "위 y", round(yt, 1), "아래 y", round(yb, 1), "닫힘", m.is_watertight)
    fc = np.tile([228, 232, 240, 255], (len(m.faces), 1)); cen = m.triangles_center
    if ST >= 2:
        for pth, yf in prisms: fc[pth.contains_points(cen[:, [0, 2]], radius=0.5) & (cen[:, 1] > yf - 1) & (cen[:, 1] < yf + DP + 1)] = [20, 20, 26, 255]
mm = trimesh.Trimesh(m.vertices, m.faces, face_colors=fc, process=False)
parts = [mm] + [trimesh.Trimesh(e.vertices, e.faces, face_colors=np.tile([140, 215, 250, 255], (len(e.faces), 1)), process=False) for e in extra]
out = trimesh.util.concatenate(parts); out.unmerge_vertices(); vc = np.zeros((len(out.vertices), 4), np.uint8)
for f, c_ in zip(out.faces, out.visual.face_colors): vc[f] = c_
trimesh.Trimesh(out.vertices, out.faces, vertex_colors=vc, process=False).export(B + nm + ".ply", encoding="ascii")
m.export(B + nm + "_몸.stl")
