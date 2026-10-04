# -*- coding: utf-8 -*-
"""머리 솔리드 S 판 (10-05 · 「P1 개판 · 알아서 고쳐」) — 얇은 판 겹쳐 쌓기(짜깁기) 대신 꽉 찬 덩어리 하나를 깎고 붙인다.
python 머리솔리드.py <판 번호>
  S1: 바탕 = 스트라이크 돔(1 판 · 핀 뗌)을 0.5 mm 복셀로 속까지 채운 솔리드 ∪ CAD v45 몸 앞부분(y < −20)
      → 얼굴 앞을 위에서 본 V(45°)로 깎음 → 눈 창을 눈알 깊이까지 팜
      → ∪ 두께 있는 부품(뿔 · 마스크 · 차양 · 볼 · 가시) · 안테나 Ø2 mm 막대(뿌리 8 mm 머리 안)
      → 눈알은 따로(색) · 번개(0.3 mm)는 도색
출력: 머리솔리드_S<n>.ply(흰 몸 + 파란 눈) · 머리솔리드_S<n>_몸.stl"""
import sys, os, json, numpy as np, trimesh
from scipy import ndimage
from skimage import measure
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; SC = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
N = int(sys.argv[1]); k = 60.0 / 175.0   # mm/단위(머리 60 mm)
U = lambda mm: mm / k
def L(nm):
    m = trimesh.load(SC + f"{nm}_v45.stl"); m.merge_vertices()
    if m.is_volume: return m
    ps = []   # 차양 · 볼날개 STL 이 안 닫혀 불리언이 거부(10-05) → 조각마다 구멍 메우기, 안 되면 볼록 껍질
    for p in m.split(only_watertight=False):
        trimesh.repair.fill_holes(p); trimesh.repair.fix_normals(p)
        ps.append(p if p.is_volume else p.convex_hull)
    return trimesh.boolean.union(ps, engine="manifold") if len(ps) > 1 else ps[0]
def 합(a, b): return trimesh.boolean.union([a, b], engine="manifold")
def 빼(a, b): return trimesh.boolean.difference([a, b], engine="manifold")
def 곱(a, b): return trimesh.boolean.intersection([a, b], engine="manifold")
# 돔 솔리드(한 번 굽고 저장)
DOME = B + ("돔솔리드.ply" if N < 2 else "돔속채움.ply")
if not os.path.exists(DOME):
    d = trimesh.load(B + "스트라이크_다듬기1.ply", process=False); P = U(0.5)
    lo = d.bounds[0] - 3 * P; dims = np.ceil((d.bounds[1] - d.bounds[0]) / P).astype(int) + 7; G = np.zeros(dims, bool)
    pts = np.vstack([d.sample(int(d.area / P / P * 6)), d.vertices]); idx = np.floor((pts - lo) / P).astype(int); G[tuple(idx.T)] = True
    G = ndimage.binary_dilation(G)
    for z in range(G.shape[2]): G[:, :, z] = ndimage.binary_fill_holes(G[:, :, z])
    for y in range(G.shape[1]): G[:, y, :] = ndimage.binary_fill_holes(G[:, y, :])
    lab, nl = ndimage.label(G); G = lab == (np.argmax(ndimage.sum(G, lab, range(1, nl + 1))) + 1)
    if N >= 2: G = ndimage.binary_erosion(G, iterations=4)   # S2: 복셀 겉은 쭈글쭈글 → 속 채움만 2 mm 안으로 줄이고 겉은 원본 껍질(아래 ∪)
    v, f, _, _ = measure.marching_cubes(ndimage.gaussian_filter(np.pad(G, 2).astype(np.float32), 1.0), 0.5); v = (v - 2) * P + lo
    dm = trimesh.Trimesh(v, f, process=True)
    if dm.volume < 0: dm.invert()
    import fast_simplification
    vv, ff = fast_simplification.simplify(dm.vertices, dm.faces, target_reduction=max(0, 1 - 40000 / len(dm.faces)))
    dm = trimesh.Trimesh(vv, ff, process=True); trimesh.repair.fix_normals(dm); dm.export(DOME); print("돔 솔리드", len(dm.faces), dm.is_watertight)
dome = trimesh.load(DOME)
if N >= 2:   # S2: 겉 = 스트라이크 원래 매끈한 껍질(닫힌 얇은 볼륨) ∪ 2 mm 줄인 속 채움
    sh = trimesh.load(B + "스트라이크_정렬.ply", process=False); sh = trimesh.Trimesh(sh.vertices, sh.faces)   # PLY 로 저장 · 읽기에서 닫힘이 깨져 1 판(핀 떼기)을 여기서 다시
    C_ = np.array([14.0, 40.0, -200.0]); R_ = np.array([78.0, 95.0, 95.0])
    ell = trimesh.creation.icosphere(4); ell.apply_scale(R_); ell.apply_translation(C_)
    bx = trimesh.creation.box(extents=[2 * R_[0], 2 * R_[1], 120]); bx.apply_translation([C_[0], C_[1], C_[2] - 60])
    sh = 곱(sh, 합(ell, bx))
    dome = 합(sh, dome)
body = L("body"); front = trimesh.creation.box(extents=[400, 400, 600]); front.apply_translation([0, -20 - 200, -150])
base = 합(dome, 곱(body, front))
# 얼굴 V(45°): 꼭짓점 = 얼굴판 앞 끝 y, 옆으로 |x| 만큼 물러남 · 얼굴 높이(눈썹 V 아래)만
fp = L("faceplate"); yk = fp.bounds[0][1]; zt = fp.bounds[1][2]; zb = fp.bounds[0][2]
def vprism(y0):
    from shapely.geometry import Polygon
    pg = Polygon([(0, y0), (300, y0 + 300), (300, 600), (-300, 600), (-300, y0 + 300)])
    p = trimesh.creation.extrude_polygon(pg, zt - zb + 2); p.apply_translation([0, 0, zb - 1]); return p
얼굴띠 = trimesh.creation.box(extents=[400, 400, zt - zb]); 얼굴띠.apply_translation([0, 0, (zt + zb) / 2])
base = 빼(base, 빼(곱(base, 얼굴띠), vprism(yk)))
# 눈 창 파기: 눈 창 윤곽 기둥을 앞에서 눈알 중심 깊이까지
V = json.load(open(SC + "v3.json", encoding="utf-8")); W = json.load(open(SC + "eyewin.json", encoding="utf-8"))["왼"]
eye = L("eye"); ey = eye.bounds.mean(0)[1]
from shapely.geometry import Polygon
for P_ in (W, [[-x, z] for x, z in W][::-1]):
    pr = trimesh.creation.extrude_polygon(Polygon(P_).buffer(0), 400)   # (x, z) 다각형을 y 로: 돌려 놓기
    pr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); pr.apply_translation([0, ey + 2 - 0, 0])
    base = 빼(base, pr)
# 두께 있는 부품
for nm in (("horn", "mask", "visor", "spike") if N >= 3 else ("horn", "mask", "visor", "cheek", "spike")):   # S3: 볼날개 띠는 스트라이크 돔 위에서 떠 보여 뺌(원화 볼은 가시 말고 밋밋)
    base = 합(base, L(nm))
# 안테나 Ø2 mm 막대(뿌리 8 mm 머리 안)
cc = base.centroid
for a_ in L("antenna").split():
    v = a_.vertices; c0 = v.mean(0); ax = np.linalg.svd(v - c0)[2][0]; t = (v - c0) @ ax; a, e = v[t.argmin()], v[t.argmax()]
    if np.linalg.norm(a - cc) > np.linalg.norm(e - cc): a, e = e, a
    a = a + (cc - a) / np.linalg.norm(cc - a) * U(8.0)
    base = 합(base, trimesh.creation.cylinder(radius=U(1.0), segment=[a, e], sections=16))
print("몸", len(base.faces), "닫힘", base.is_watertight, "몸체", len(base.split(only_watertight=False)), "부피 mm³", round(base.volume * k ** 3))
base.export(B + f"머리솔리드_S{N}_몸.stl")
w = base.copy(); w.visual.vertex_colors = np.tile([228, 232, 240, 255], (len(w.vertices), 1)).astype(np.uint8)
if N >= 3:   # S3: 눈 창 안쪽 면 = 도색(검정) — 면 중심이 눈 창 윤곽 안 · 얼굴 겉보다 뒤
    from matplotlib.path import Path as _P
    w = trimesh.Trimesh(w.vertices, w.faces, process=False); fc = np.tile([228, 232, 240, 255], (len(w.faces), 1))
    cen = w.triangles_center
    for P_ in (W, [[-x, z] for x, z in W][::-1]):
        inn = _P(np.array(P_)).contains_points(cen[:, [0, 2]], radius=-0.5)
        fc[inn & (cen[:, 1] > yk + 2)] = [20, 20, 26, 255]
    w.visual.face_colors = fc
eye.visual.vertex_colors = np.tile([140, 215, 250, 255], (len(eye.vertices), 1)).astype(np.uint8)
ex = [w, eye]
if N >= 2:   # 눈 창 안 = 도색 자리 → 렌더에서도 검게(소켓 v45 · 출력물엔 안 들어감)
    so = L("socket"); so.visual.vertex_colors = np.tile([20, 20, 26, 255], (len(so.vertices), 1)).astype(np.uint8); ex.append(so)
trimesh.util.concatenate(ex).export(B + f"머리솔리드_S{N}.ply")
