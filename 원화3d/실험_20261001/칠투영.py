# -*- coding: utf-8 -*-
"""디테일 1 바퀴 — 원화 칠 투영 (10-04 사용자 「형태는 갖춰가고 있어 · 이제는 디테일이 문제」).
렌즈: BOME 「조형 7 : 도색 3 · 칠하지 않으면 회색 덩어리」 · 와타나베 「밀도를 올릴수록 멋있다 · 그림자를 도장에 옮기지 말 것」.
앞을 보는 면(법선 y < −0.2)만 정면 원화(판_1)의 그 자리 색을 **다섯 칠**로 나눠 칠한다(그림자 · 명암은 옮기지 않음):
  검정(밝기 < 55: 눈구멍 · 먹) · 파랑(채도 높고 색상 95~130: 번개) · 노랑(색상 15~40 · 채도 > 60: 안테나 · 뿔 금) · 눈 하늘색(눈 윤곽 안 · 밝기 ≥ 55) · 나머지 흰 갑주
면 중심 하나 대신 면 안 세 점(꼭짓점 쪽으로 1/3)의 다수결 — 작은 면도 자기 칸 색을 받게. 옆을 보는 면은 흰 갑주 그대로.
python 칠투영.py <입력 ply> <출력 ply>"""
import os, sys, json, numpy as np, cv2, trimesh
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
art = cv2.imdecode(np.fromfile(os.path.join(A, "판_1_원화.png"), np.uint8), 1); H, W = art.shape[:2]
hsv = cv2.cvtColor(art, cv2.COLOR_BGR2HSV); lab = cv2.cvtColor(art, cv2.COLOR_BGR2LAB)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
눈 = np.zeros((H, W), np.uint8)
for P in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).values(): cv2.fillPoly(눈, [np.round(np.array(P)).astype(np.int32)], 1)
칠 = {0: (232, 234, 244), 1: (22, 22, 28), 2: (60, 110, 220), 3: (205, 175, 70), 4: (140, 200, 235)}
L, Hh, S = lab[:, :, 0].astype(int), hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int)
분류 = np.zeros((H, W), np.uint8)
분류[(Hh >= 95) & (Hh <= 130) & (S > 90)] = 2
분류[(Hh >= 15) & (Hh <= 40) & (S > 60)] = 3
분류[L < 55] = 1
검덩이 = cv2.morphologyEx((L < 55).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0   # 디테일 2 바퀴: 가는 먹선은 칠이 아니다(1 바퀴 얼룩) — 덩어리(눈구멍)만
분류[(분류 == 1) & ~검덩이] = 0
분류[(눈 > 0) & (L >= 55)] = 4
분류[(눈 > 0) & (L < 55)] = 1
src, dst = sys.argv[1], sys.argv[2]
m = trimesh.load(os.path.join(B, src), process=False)
if os.environ.get("SUB", "1") == "1":   # 디테일 2 바퀴: 앞면만 1.5 화소로 잘게 — 면 하나에 색 하나라 칸 경계가 뭉개졌다
    앞0 = m.face_normals[:, 1] < -0.2; 앞m = m.submesh([np.nonzero(앞0)[0]], append=True); 뒤m = m.submesh([np.nonzero(~앞0)[0]], append=True)
    v_, f_ = trimesh.remesh.subdivide_to_size(앞m.vertices, 앞m.faces, max_edge=1.5)
    c_ = 앞m.visual.vertex_colors[앞m.faces][:, 0]; 원 = trimesh.Trimesh(앞m.vertices, 앞m.faces, process=False)
    _, _, tid = trimesh.proximity.closest_point(원, trimesh.Trimesh(v_, f_, process=False).triangles_center)
    잘 = trimesh.Trimesh(v_, f_, process=False); 잘.visual.face_colors = c_[tid]
    잘 = trimesh.Trimesh(잘.vertices[잘.faces].reshape(-1, 3), np.arange(len(잘.faces) * 3).reshape(-1, 3), vertex_colors=np.repeat(c_[tid], 3, 0), process=False)
    m = trimesh.util.concatenate([잘, 뒤m]); m = trimesh.Trimesh(m.vertices, m.faces, vertex_colors=m.visual.vertex_colors, process=False)
V = m.vertices[m.faces].reshape(-1, 3); C = m.visual.vertex_colors[m.faces].reshape(-1, 4).copy(); F = np.arange(len(V)).reshape(-1, 3)
tri = m.triangles; cen = tri.mean(1); 앞 = m.face_normals[:, 1] < -0.2
표 = np.stack([(2 * cen + tri[:, i]) / 3 for i in range(3)], 1)   # 면 안 세 점
px = np.clip(np.round(표[:, :, 0] + cu).astype(int), 0, W - 1); pr = np.clip(np.round(-표[:, :, 2]).astype(int), 0, H - 1)
k = 분류[pr, px]; 표결 = np.array([np.bincount(r, minlength=5).argmax() for r in k])
기존노랑 = (m.visual.vertex_colors[m.faces][:, 0, 0] > 150) & (m.visual.vertex_colors[m.faces][:, 0, 2] < 120)
새 = np.where(앞 & ~기존노랑, 표결, -1)
for c, rgb in 칠.items(): C.reshape(-1, 3, 4)[새 == c, :, :3] = rgb
trimesh.Trimesh(V, F, vertex_colors=C, process=False).export(os.path.join(B, dst), encoding="ascii")
print({이름: int((새 == c).sum()) for c, 이름 in zip(range(5), ["흰", "검정", "파랑", "노랑", "눈"])}, {"앞면": int(앞.sum()), "전체": len(m.faces)})
