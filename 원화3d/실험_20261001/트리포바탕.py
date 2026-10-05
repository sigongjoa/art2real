# -*- coding: utf-8 -*-
"""TripoSG 머리를 바탕으로(10-05 사용자 「A」) — T 판: 원본 glb(닫힘) → 같은 정렬(축 돌림 · 150 · 레퍼런스정렬 어파인) → z 컷(깃 · 어깨) → 면 단순화
python 트리포바탕.py <판 이름> [z컷=-238] [면 수=6000]"""
import sys, numpy as np, trimesh, fast_simplification
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; SCR = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/"
n = sys.argv[1]; ZC = float(sys.argv[2]) if len(sys.argv) > 2 else -238.0; NF = int(sys.argv[3]) if len(sys.argv) > 3 else 6000
s = trimesh.load("G:/art2real/트레일/trail4_gen3d/out/knights/h_Omegamon_main.glb"); m = s.to_geometry() if hasattr(s, "to_geometry") else s
v = m.vertices; v = np.c_[v[:, 0], -v[:, 2], v[:, 1]]
src = trimesh.load(B + "트리포원본.ply", process=False).vertices   # 같은 정규화(중심 · 150) 재현: 원본 ply 는 2 만 면 단순화본이라 중심 · 배율을 그 범위로
raw = trimesh.load(SCR + "tripo_raw.ply", process=False).vertices; raw = np.c_[raw[:, 0], -raw[:, 2], raw[:, 1]]
c0 = raw.mean(0); s0 = 150 / (raw[:, 2].max() - raw[:, 2].min())
v = (v - c0) * s0
A = np.load(SCR + "tripo_affine.npy"); v = np.c_[v, np.ones(len(v))] @ A
m = trimesh.Trimesh(v, m.faces, process=True); print("원본", len(m.faces), m.is_watertight)
m = m.slice_plane([0, 0, ZC], [0, 0, 1], cap=True); print("컷", m.is_watertight, m.bounds.round(0).tolist())
if n >= "트리포_T2":   # T2: z 컷만으론 옆 깃 · 뒤 망토 판이 남음 → 머리 타원체 ∪ 뿔 · 안테나 상자 와 교집합
    el = trimesh.creation.icosphere(4); el.apply_scale([82, 100, 62]); el.apply_translation([5, 10, -195])
    bx = trimesh.creation.box(extents=[160, 127, 115]); bx.apply_translation([35, -48.5, -117.5])
    m = trimesh.boolean.intersection([m, trimesh.boolean.union([el, bx], engine="manifold")], engine="manifold"); print("머리만", m.is_watertight, m.bounds.round(0).tolist())
if n == "트리포_T3":   # (T3 만 · 뿔이 옆으로 기울어 생성돼 거울하면 뿔이 사라짐 — 버림) T3: 뒤 아래 망토 판 자르기 · 거울 겹침 최대 대칭면 x = c 찾아 깃 적은 반쪽을 거울
    cape = trimesh.creation.box(extents=[400, 200, 200]); cape.apply_translation([0, 25 + 100, -212 - 100])
    m = trimesh.boolean.difference([m, cape], engine="manifold")
    P = m.sample(20000); best = None
    for c in np.arange(-20, 40, 1.0):
        Q = P.copy(); Q[:, 0] = 2 * c - Q[:, 0]
        d = trimesh.proximity.ProximityQuery(m).signed_distance(Q[::10]) if False else None
        from scipy.spatial import cKDTree
        dd, _ = cKDTree(P).query(Q[::5]); sc = np.median(dd)
        if best is None or sc < best[0]: best = (sc, c)
    c = best[1]; print("대칭면 x", c, "거울 거리 중앙", round(best[0], 2))
    vol = lambda h: h.volume
    L = trimesh.boolean.intersection([m, trimesh.creation.box(bounds=[[-400, -400, -400], [c, 400, 400]])], engine="manifold")
    R = trimesh.boolean.intersection([m, trimesh.creation.box(bounds=[[c, -400, -400], [400, 400, 400]])], engine="manifold")
    wL = np.abs(L.vertices[:, 0] - c).max(); wR = np.abs(R.vertices[:, 0] - c).max(); print("반쪽 폭", round(wL), round(wR))
    H = L if wL <= wR else R   # 깃이 남은 쪽이 더 넓다 → 좁은 쪽을 씀
    Mi = H.copy(); Mi.vertices[:, 0] = 2 * c - Mi.vertices[:, 0]; Mi.invert()
    m = trimesh.boolean.union([H, Mi], engine="manifold"); m.vertices[:, 0] -= c   # 대칭면을 축 A(x = 0)로
if n == "트리포_T4":   # (T4 만) T4: 망토 자르기 + 깃이 남은 쪽(x < −45 · z < −185)만 자름 · 거울 없음
    for bnd in ([[-400, 25, -400], [400, 400, -212]], [[-400, -400, -400], [-45, 400, -185]]):
        m = trimesh.boolean.difference([m, trimesh.creation.box(bounds=bnd)], engine="manifold")
if n >= "트리포_T5":   # T5: 상자 자르기 대신 형태학 열기(반지름 6) — 얇은 깃 · 망토 판은 지워지고 두꺼운 머리는 남음 · 뿔 · 안테나 · 돔 위는 원본 z > −165 를 다시 합침
    from scipy import ndimage
    from skimage import measure
    P_ = 1.0; lo = m.bounds[0] - 8; vg = m.voxelized(P_).fill(); G = vg.matrix; o0 = vg.translation
    st = ndimage.generate_binary_structure(3, 1); G2 = ndimage.binary_opening(G, structure=st, iterations=6)
    lab, nl = ndimage.label(G2); G2 = lab == (np.argmax(ndimage.sum(G2, lab, range(1, nl + 1))) + 1)
    vv_, ff_, _, _ = measure.marching_cubes(ndimage.gaussian_filter(np.pad(G2, 2).astype(np.float32), 1.0), 0.5)
    hd = trimesh.Trimesh((vv_ - 2) * P_ + o0, ff_, process=True)
    if hd.volume < 0: hd.invert()
    keep = trimesh.creation.box(bounds=[[-400, -400, -165], [400, 400, 400]])
    if n >= "트리포_T6": keep = trimesh.boolean.union([keep, trimesh.creation.box(bounds=[[-60, -400, -240], [85, -40, -165]])], engine="manifold")   # T6: 열기가 눈 · 부리까지 뭉갬 → 얼굴 앞도 원본
    top = trimesh.boolean.intersection([m, keep], engine="manifold")
    m = trimesh.boolean.union([hd, top], engine="manifold"); print("열기", nl, "덩어리 · 합침", m.is_watertight)
vv, ff = fast_simplification.simplify(m.vertices, m.faces, target_reduction=1 - NF / len(m.faces))
m = trimesh.Trimesh(vv, ff, process=True); trimesh.repair.fix_normals(m)
parts = m.split(only_watertight=False); m = max(parts, key=lambda p: p.area)   # 떨어진 부스러기 버림
print(n, len(m.faces), "닫힘", m.is_watertight)
m.visual.vertex_colors = np.tile([228, 232, 240, 255], (len(m.vertices), 1)).astype(np.uint8); m.export(B + n + ".ply")
