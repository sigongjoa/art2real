# -*- coding: utf-8 -*-
"""O16 출력 문턱 (10-05 · 원형사 패널 「크기 먼저 · 출력은 문턱」) — 실물 mm 로 잰다.
python 출력문턱.py <ply 이름(블렌더 폴더)> [머리 mm=60] [머리 단위 높이=175]
  몸체(연결 성분)마다: 닫힘 · 두께(면 중심에서 안쪽 법선으로 광선 → 같은 몸체 반대 면까지) · 바닥판 256 mm
  몸체 사이: 겹침(서로 안으로 파고든 꼭짓점 수)
  문턱: 벽 ≥ 1.2 mm(얇은 면이 몸체 면적의 1 % 넘으면 불통과 — 뿔 끝 같은 뾰족한 끝은 허용)(가는 막대도 같은 광선 두께로 잡힘 · 지름 ≥ 2 는 1.2 에 포함해 본다 — ponytail: 막대 지름 따로 재기는 필요해지면)
출력: <이름>_문턱.json · <이름>_문턱.ply(얇은 면 빨강 · 통과 회색) · 표 출력"""
import os, sys, json, numpy as np, trimesh
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"
n = sys.argv[1]; MM = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0; HU = float(sys.argv[3]) if len(sys.argv) > 3 else 175.0
k = MM / HU; WALL = 1.2; BED = 256.0
m = trimesh.load(B + n + ".ply", process=False); m = trimesh.Trimesh(m.vertices * k, m.faces, process=True)   # mm 로
bodies = m.split(only_watertight=False)
rows = []; thin_all = []; parts = []
for i, b in enumerate(bodies):
    c = b.triangles_center; nr = b.face_normals
    sel_ = np.arange(len(c)) if len(c) <= 20000 else np.random.default_rng(0).choice(len(c), 20000, replace=False)   # 15 만 면 전부 광선은 10 분 넘음 → 2 만 표본
    o = c[sel_] - nr[sel_] * 1e-3
    loc, ri, _ = b.ray.intersects_location(o, -nr[sel_], multiple_hits=False)
    t = np.full(len(sel_), np.inf); t[ri] = np.linalg.norm(loc - o[ri], axis=1)
    thin_s = t < WALL; area = b.area_faces[sel_]; thin = np.zeros(len(c), bool); thin[sel_] = thin_s
    rows.append({"몸체": i, "면": len(b.faces), "닫힘": bool(b.is_watertight), "크기 mm": b.extents.round(1).tolist(),
                 "얇은 면 %": round(100 * area[thin_s].sum() / area.sum(), 1), "최소 두께 mm": round(float(np.min(t)), 2) if np.isfinite(t).any() else None})
    col = np.tile([200, 200, 205, 255], (len(b.faces), 1)); col[thin] = [230, 40, 40, 255]
    q = b.copy(); q.visual.face_colors = col; parts.append(q)
# 겹침: 몸체 j 의 꼭짓점이 닫힌 몸체 i 안에 있는 수
겹 = 0; 겹짝 = []
closed = [(i, b) for i, b in enumerate(bodies) if b.is_watertight]
for i, bi in closed:
    for j, bj in enumerate(bodies):
        if i == j: continue
        bb = bi.bounds; v = bj.vertices; sel = np.all((v >= bb[0]) & (v <= bb[1]), axis=1)
        if not sel.any(): continue
        inside = bi.contains(v[sel]).sum()
        if inside: 겹 += int(inside); 겹짝.append((i, j, int(inside)))
ext = m.extents
판정 = {"이름": n, "mm/단위": round(k, 3), "몸체 수": len(bodies), "닫히지 않은 몸체": sum(not r["닫힘"] for r in rows),
      "얇은 면 있는 몸체": sum(r["얇은 면 %"] > 1.0 for r in rows), "겹친 꼭짓점": 겹, "전체 크기 mm": ext.round(1).tolist(), "바닥판 안": bool((ext <= BED).all())}
판정["통과"] = 판정["닫히지 않은 몸체"] == 0 and 판정["얇은 면 있는 몸체"] == 0 and 겹 == 0 and 판정["바닥판 안"]
json.dump({"판정": 판정, "몸체": rows, "겹친 짝": 겹짝[:50]}, open(B + n + "_문턱.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
out = trimesh.util.concatenate(parts); out.vertices /= k   # 렌더 틀은 원래 단위로
fc = out.visual.face_colors; vc = np.zeros((len(out.vertices), 4), np.uint8)
for f, c_ in zip(out.faces, fc): vc[f] = np.maximum(vc[f], c_)   # 꼭짓점 색(빨강 우선)
trimesh.Trimesh(out.vertices, out.faces, vertex_colors=vc, process=False).export(B + n + "_문턱.ply", encoding="ascii")
print(json.dumps(판정, ensure_ascii=False, default=str))
for r in sorted(rows, key=lambda r: -r["얇은 면 %"])[:8]: print(r)
if __name__ == "__main__" and os.environ.get("ASSERT_FAIL"):   # 질 수 있는 문턱 확인용
    assert not 판정["통과"], "문턱이 질 수 없다 — 불통과여야 할 판이 통과"
