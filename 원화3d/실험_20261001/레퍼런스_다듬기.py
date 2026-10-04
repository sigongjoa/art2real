# -*- coding: utf-8 -*-
"""레퍼런스 다듬기(10-05 · 후보 2 빌드스트라이크만으로) — 판마다 하나씩: STEP 환경변수로 몇 단계까지.
  1 V 핀 넷 떼기: 남길 부피 = 돔 타원체(위) ∪ 상자(아래) 와 교집합(manifold)
  3 (2b) 외뿔 = CAD v45 지느러미 뿔(원화 치수)
  2 외뿔: 페넥스 뿔(Printables 1003283 · CC0) 두 날을 맞대 두께 6 → x 축으로 세워 70°(앞으로 20° 기욺) → 끝이 원화 뿔 끝 z −2 에 닿게 배율 → 밑동을 이마 겉(z −165)에 3 묻음
입력 스트라이크_정렬.ply → 출력 스트라이크_다듬기<STEP>.ply"""
import os, numpy as np, trimesh
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"; STEP = int(os.environ.get("STEP", "1"))
m = trimesh.load(os.path.join(B, "스트라이크_정렬.ply"), process=False); m = trimesh.Trimesh(m.vertices, m.faces)
C = np.array([14.0, 40.0, -200.0]); R = np.array([78.0, 95.0, 95.0])
if STEP >= 1:
    ell = trimesh.creation.icosphere(4); ell.apply_scale(R); ell.apply_translation(C)
    box = trimesh.creation.box(extents=[2 * R[0], 2 * R[1], 120]); box.apply_translation([C[0], C[1], C[2] - 60])
    keep = trimesh.boolean.union([ell, box], engine="manifold")
    m = trimesh.boolean.intersection([m, keep], engine="manifold")
if STEP == 8:   # (8 만 · 뒷걸음이라 되돌림) 8: 스트라이크 귀 원통(중심에서 |x| > 67 · y 23~88 · z −230~−175) — 원화 돔은 매끈
    for sg in (1, -1):
        bx = trimesh.creation.box(extents=[40, 80, 65]); bx.apply_translation([C[0] + sg * (67 + 20), 55, -202])
        m = trimesh.boolean.difference([m, bx], engine="manifold")
m0 = m.copy()   # 뿔 붙이기 전 투구
if STEP >= 3:   # 2b(=3): 페넥스 날은 톱니 여럿 · 정면 가는 선 → CAD v45 에서 원화 치수로 지은 지느러미 뿔을 옮겨 꽂음(x 가운데만 머리 중심으로)
    h = trimesh.load("C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/horn_v45.stl")
    h.apply_translation([C[0] - h.bounds.mean(0)[0], 0, 0]); print("뿔 v45", h.bounds.round(1).tolist())
    m = trimesh.boolean.union([m, h], engine="manifold")
elif STEP >= 2:
    H = trimesh.load("G:/art2real/원화3d/out/레퍼런스/투구/페넥스뿔.stl"); ps = H.split(only_watertight=False)
    hs = []
    for p_, sx in zip(ps, (-1, 1)):
        p_ = p_.copy(); p_.apply_translation([sx * 1.5 - p_.bounds.mean(0)[0], 0, 0]); hs.append(p_)
    h = trimesh.boolean.union(hs, engine="manifold")
    v0 = h.vertices; c0 = v0.mean(0); ax = np.linalg.svd(v0 - c0)[2][0]; t = (v0 - c0) @ ax
    base, tip = v0[t.argmin()], v0[t.argmax()]
    if tip[2] < base[2]: base, tip = tip, base
    a_now = np.arctan2(tip[2] - base[2], tip[1] - base[1]); a_want = np.radians(180 - 70)
    h.apply_translation(-base); h.apply_transform(trimesh.transformations.rotation_matrix(a_want - a_now, [1, 0, 0]))
    zb = -165.0; zt = -2.0; s_ = (zt - zb) / h.vertices[:, 2].max(); h.apply_scale(s_)
    yb = m.ray.intersects_location([[C[0], -400, zb]], [[0, 1, 0]], multiple_hits=False)[0][0][1] + 3
    h.apply_translation([C[0], yb, zb]); print("뿔", h.bounds.round(1).tolist(), "배율", round(s_, 2))
    m = trimesh.boolean.union([m, h], engine="manifold")
core = None
if STEP == 4:   # 4b(실패 · 기록용): 속 = 투구 볼록 껍질 0.94 배 − 투구 — 오목한 곳마다 뚫고 나옴
    hull = m0.convex_hull; cc = hull.centroid
    ci = hull.copy(); ci.apply_translation(-cc); ci.apply_scale(0.94); ci.apply_translation(cc)
    core = trimesh.boolean.difference([ci, m0], engine="manifold"); print("속", core.bounds.round(1).tolist())
parts = []
if STEP >= 5:   # 5: 착용 투구의 얼굴 창 자리를 CAD 얼굴 구멍 기둥으로 도려내고 CAD v45 얼굴 부품(원화 치수)을 넣음 · 속(4 판)은 쓰지 않음
    import json
    from shapely.geometry import Polygon
    SC = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
    V = json.load(open(SC + "v3.json", encoding="utf-8"))
    for P in V["얼굴 구멍"]:
        pr = trimesh.creation.extrude_polygon(Polygon(P).buffer(0), 400)   # XY 평면 다각형을 +Z 로 → (x, z) 다각형을 y 로 밀게 돌림
        pr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); pr.apply_translation([0, V["E"]["y0"], 0])
        m = trimesh.boolean.difference([m, pr], engine="manifold")
    col = {"antenna": (210, 175, 60)} if STEP >= 7 else {}
    col.update({"faceplate": (228, 232, 244), "eye": (140, 215, 250), "socket": (20, 20, 26), "mask": (214, 218, 232), "visor": (222, 226, 240), "cheek": (220, 224, 238), "spike": (226, 230, 244), "bolt": (40, 110, 235)})   # 7: 안테나 둘(CAD v45 · 원화 정면 방향)
    for nm, c in col.items():
        q = trimesh.load(SC + f"{nm}_v45.stl"); q.visual.vertex_colors = np.tile(list(c) + [255], (len(q.vertices), 1)).astype(np.uint8); parts.append(q)
    if STEP >= 6:   # 6: 얼굴(−98)과 투구 앞(−55) 사이 틈 → CAD v45 투구 · 검은 속의 앞부분(y < −30)을 다리로
        cut = trimesh.creation.box(extents=[400, 400, 600]); cut.apply_translation([0, -30 - 200, -150])
        for nm, c in (("helmet", (232, 234, 244)), ("core", (30, 30, 36))):
            q = trimesh.boolean.intersection([trimesh.load(SC + f"{nm}_v45.stl"), cut], engine="manifold")
            q.visual.vertex_colors = np.tile(list(c) + [255], (len(q.vertices), 1)).astype(np.uint8); parts.append(q); print(nm, "앞", q.bounds.round(1).tolist())
print(STEP, len(m.faces), m.bounds.round(1).tolist(), m.is_watertight)
m.visual.vertex_colors = np.tile([228, 232, 240, 255], (len(m.vertices), 1)).astype(np.uint8)
for q in parts: m = trimesh.util.concatenate([m, q])
if core is not None:
    core.visual.vertex_colors = np.tile([30, 30, 36, 255], (len(core.vertices), 1)).astype(np.uint8)
    m = trimesh.util.concatenate([m, core])
m.export(os.path.join(B, f"스트라이크_다듬기{STEP}.ply"))
