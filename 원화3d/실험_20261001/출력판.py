# -*- coding: utf-8 -*-
"""출력판 P1 (10-05 · 원형사 패널: 24 Brite 「한 덩어리」 · 메모리 「굿즈 속은 차도 된다」 · 머리 60 mm)
python 출력판.py <입력 ply> <출력 이름> [머리 mm=60] [머리 단위 높이=175]
  ① 금색(안테나) 몸체를 빼고 지름 2 mm 막대로 바꿈(같은 뿌리 → 끝)
  ② 모든 몸체의 겉을 0.3 mm 복셀로 찍고 1 칸 불림 → z 단면마다 닫힌 고리 안을 채움(얇은 착용 투구 껍질 · 겹침 · 열린 몸체가 한 덩어리로)
  ③ 마칭큐브 → 타우빈 다듬기(계단 줄이기 · 부피 유지) → 원래 단위로 되돌려 저장"""
import sys, numpy as np, trimesh
from scipy import ndimage
from skimage import measure
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"
src, dst = sys.argv[1], sys.argv[2]; MM = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0; HU = float(sys.argv[4]) if len(sys.argv) > 4 else 175.0
k = MM / HU; P = 0.3 / k   # 복셀 0.3 mm (단위)
m = trimesh.load(B + src + ".ply", process=False)
vc = m.visual.vertex_colors[:, :3].astype(int)
bodies = trimesh.Trimesh(m.vertices, m.faces, vertex_colors=m.visual.vertex_colors, process=True).split(only_watertight=False)
keep, rods = [], []
allc = np.array(m.vertices).mean(0)
for b in bodies:
    c = b.visual.vertex_colors[:, :3].mean(0)
    if c[0] > 180 and c[1] > 140 and c[2] < 100:   # 금색 = 안테나
        v = b.vertices; cc = v.mean(0); ax = np.linalg.svd(v - cc)[2][0]; t = (v - cc) @ ax
        a, e = v[t.argmin()], v[t.argmax()]
        if np.linalg.norm(a - allc) > np.linalg.norm(e - allc): a, e = e, a   # a = 머리 쪽 뿌리
        a = a + (allc - a) / np.linalg.norm(allc - a) * (8.0 / k)   # 뿌리를 머리 안으로 8 mm(10-05: 왼 안테나가 떨어진 조각이라 버려졌다)
        r = trimesh.creation.cylinder(radius=1.0 / k, segment=[a, e], sections=16); rods.append(r)
    else:
        keep.append(b)
print("몸체", len(bodies), "안테나 → 막대", len(rods))
allm = trimesh.util.concatenate(keep + rods)
lo = allm.bounds[0] - 3 * P; dims = np.ceil((allm.bounds[1] - allm.bounds[0]) / P).astype(int) + 7
G = np.zeros(dims, bool)
for b in keep + rods:
    pts = b.sample(int(b.area / (P * P) * 6) + 2000)   # 겉을 촘촘히 찍음
    pts = np.vstack([pts, b.vertices]); idx = np.floor((pts - lo) / P).astype(int)
    G[idx[:, 0], idx[:, 1], idx[:, 2]] = True
G = ndimage.binary_dilation(G, iterations=1)
for z in range(G.shape[2]): G[:, :, z] = ndimage.binary_fill_holes(G[:, :, z])
for y in range(G.shape[1]): G[:, y, :] = ndimage.binary_fill_holes(G[:, y, :])   # 옆 단면도 한 번(돔 꼭대기 고리가 안 닫힐 때)
G = ndimage.binary_closing(G, iterations=1)
lab, nl = ndimage.label(G); sizes = ndimage.sum(G, lab, range(1, nl + 1)); G = lab == (np.argmax(sizes) + 1)   # 가장 큰 덩어리만
print("복셀", G.shape, "덩어리", nl, "→ 1")
F_ = ndimage.gaussian_filter(np.pad(G, 2).astype(np.float32), 1.0)   # 이진 그대로면 대각선 연결에서 면이 갈라져 19 조각 · 안 닫힘 → 흐린 장에서 0.5 등면
v, f, _, _ = measure.marching_cubes(F_, 0.5)
v = (v - 2) * P + lo
out = trimesh.Trimesh(v, f, process=True)
if out.volume < 0: out.invert()   # 마칭큐브 면 방향이 안쪽이었다(부피 음수)
import fast_simplification
vv, ff = fast_simplification.simplify(out.vertices, out.faces, target_reduction=1 - 150000 / len(out.faces))   # 91 만 면 → 15 만(문턱 · 슬라이서가 느렸다)
out = trimesh.Trimesh(vv, ff, process=True); trimesh.repair.fix_normals(out); trimesh.smoothing.filter_taubin(out, iterations=12)
out.visual.vertex_colors = np.tile([228, 232, 240, 255], (len(out.vertices), 1)).astype(np.uint8)
out.export(B + dst + ".ply"); print(dst, len(out.faces), "닫힘", out.is_watertight, "몸체", len(out.split(only_watertight=False)), "부피 mm³", round(out.volume * k ** 3))
