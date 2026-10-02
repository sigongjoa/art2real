# -*- coding: utf-8 -*-
"""분할 시험 사다리 (10-02 사용자 「각 분할하는 과정과 원래 것이랑 제대로 되는지 · 쉬운 예제부터 어려운 예제까지」).
정답을 아는 부품 모음을 정확한 불리언 합집합(manifold)으로 한 덩어리로 녹이고 → 면분할.나누기(오목 모서리만 자름) → 면마다 정답(가장 가까운 원래 부품)과 채점.
  L1 샘플 따로(연결 성분 · 점검)  L2 샘플 녹임(CC0 메크 머리 5)  L3 더미 3판 녹임(각진 판)  L4 더미 4판 녹임(곡면 · 휜 판)  L5 오메가몬 TripoSG(정답 없음)
문턱은 30° 고정으로 보여 주고, 20 · 45 는 표에만(시험에 맞춰 고르지 않는다).
출력: out/오메가몬2/지표/분할시험/<단계>_{덩어리,자름,조각,정답,틀림}.ply · 점수.json → 분할시험_렌더.py"""
import os, sys, glob, json, numpy as np, trimesh
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 면분할 as F
R = r"G:\art2real\원화3d\out"; O = os.path.join(R, "오메가몬2", "지표", "분할시험"); os.makedirs(O, exist_ok=True)
S = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\7cb277a7-139e-42d2-8434-a71e5084b8ad\scratchpad\cut\h_remesh.obj"
rng = np.random.RandomState(3); PAL = (rng.rand(512, 3) * 0.6 + 0.35); PAL[0] = (0.55, 0.75, 1.0)

def 단계들():
    smp = sorted(glob.glob(os.path.join(R, "샘플", "메크머리_CC0", "지온", "자세_*.obj")))
    yield "L1_샘플따로", [trimesh.load(f, force="mesh") for f in smp], "따로", 215
    yield "L2_샘플녹임", [trimesh.load(f, force="mesh") for f in smp], "녹임", 215
    for v, seed in ((3, 0), (3, 1), (4, 0), (4, 1)):
        fs = sorted(glob.glob(os.path.join(R, "오메가몬2", "지표", f"더미머리{v if v == 3 else 4}", "정답", f"d{seed:03d}", "*.obj")))
        if v == 3: fs = sorted(glob.glob(os.path.join(R, "오메가몬2", "지표", "더미머리3", "정답", f"d{seed:03d}", "*.obj")))
        yield f"L{v}_더미{v}판_d{seed}", [trimesh.load(f, force="mesh") for f in fs], "녹임", 35

def 정답(u, parts):
    from scipy.spatial import cKDTree   # 부품 표면 점 표본 · 면 중심에서 가장 가까운 부품 (정확 거리는 메모리 7.8 GB 라 못 씀)
    c = u.triangles_center; d = np.stack([cKDTree(np.r_[p.vertices, p.triangles_center, trimesh.sample.sample_surface_even(p, 60000)[0]]).query(c)[0] for p in parts], 1)
    return d.argmin(1)

def ply(m, col, name):
    q = m.copy(); q.unmerge_vertices(); fc = (np.clip(col, 0, 1) * 255).astype(np.uint8)
    q.visual.vertex_colors = np.c_[np.repeat(fc, 3, 0), np.full(len(fc) * 3, 255, np.uint8)]; q.export(os.path.join(O, name + ".ply"))

점수 = {}
for 이름, parts, 방식, yaw in 단계들():
    parts = [p for p in parts if len(p.faces)]
    for p in parts:   # 거울(scale −1)로 지은 부품은 면 방향이 뒤집혀 부피가 음수 → 바로잡음
        p.merge_vertices()
        if not p.is_watertight: trimesh.repair.fill_holes(p)
        p.fix_normals()
        assert p.is_volume or 방식 == "따로", 이름
    if 방식 == "따로":
        u = trimesh.util.concatenate(parts); gt = np.repeat(np.arange(len(parts)), [len(p.faces) for p in parts])
        lab = trimesh.graph.connected_component_labels(u.face_adjacency, node_count=len(u.faces)); cut = np.zeros(len(u.faces), bool)
        표 = {"성분": F.채점(lab, gt, u.area_faces)}
    else:
        u = trimesh.boolean.union(parts, engine="manifold"); gt = 정답(u, parts); 표 = {}
        for t in (20, 30, 45): 표[t] = F.채점(*[F.나누기(u, t, 0, 0.004)[0], gt, u.area_faces])
        lab, cut = F.나누기(u, 30, 0, 0.004)
    r = 표.get(30, 표.get("성분"))
    # 틀림: 조각의 다수 정답과 면의 정답이 다른 면
    maj = np.array([np.bincount(gt[lab == s], weights=u.area_faces[lab == s]).argmax() for s in range(lab.max() + 1)])
    bad = maj[lab] != gt
    n = len(u.faces); gray = np.full((n, 3), 0.75)
    ply(u, gray, f"{이름}_덩어리"); ply(u, np.where(cut[:, None], [0.9, 0.15, 0.15], gray), f"{이름}_자름")
    ply(u, PAL[lab % 512], f"{이름}_조각"); ply(u, PAL[(gt + 7) % 512], f"{이름}_정답"); ply(u, np.where(bad[:, None], [0.9, 0.15, 0.15], [0.85, 0.85, 0.85]), f"{이름}_틀림")
    점수[이름] = {"부품수": len(parts), "면": n, "yaw": yaw, "틀린면적비": round(float(u.area_faces[bad].sum() / u.area_faces.sum()), 3),
                **{str(k): {kk: vv for kk, vv in v.items() if kk != "부품별"} for k, v in 표.items()}}
    print(이름, 점수[이름])
# L5 오메가몬: 정답 없음 · 생성 메시라 k=1(끊긴 오목 선 잇기) · M(x, y아래, z앞) → 블렌더(x, -z, -y)
m = trimesh.load(S, process=True); v = m.vertices.copy(); m.vertices = np.c_[v[:, 0], -v[:, 2], -v[:, 1]]
lab, cut = F.나누기(m, 30, 1, 0.004); n = len(m.faces); gray = np.full((n, 3), 0.75)
ply(m, gray, "L5_오메가몬_덩어리"); ply(m, np.where(cut[:, None], [0.9, 0.15, 0.15], gray), "L5_오메가몬_자름"); ply(m, PAL[lab % 512], "L5_오메가몬_조각")
점수["L5_오메가몬"] = {"면": n, "조각": int(lab.max() + 1), "yaw": 35}; print("L5", 점수["L5_오메가몬"])
json.dump(점수, open(os.path.join(O, "점수.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
