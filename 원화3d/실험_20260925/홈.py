# -*- coding: utf-8 -*-
"""규칙 패널라인 홈 — 원화에서는 「빠진 패널 · 단차 선이 어디쯤 몇 개」만 읽고, 모양은 규칙으로 짓는다 (2026-09-26).

    python 홈.py
      -> out/출력/오메가몬_PG/디자인/홈/*.stl (같은 이름 = 덮어쓰는 부품) · 부품.json · 홈.json · 홈.png
      디테일대조.py --색분할 --돌출 --홈 으로 잰다.

09-25 교훈(메모리 panel-lines-are-designed-not-traced): 먹선을 따라 판 홈은 「사람이 디자인한 느낌이 아니다」. 그래서
  1 위치만: 디테일 대조에서 빠진(모델 선 2 mm 밖) 원화 ② 패널 · ③ 단차무늬 선분, 길이 ≥ 3 mm.
  2 방향 = 0 · 45 · 90 · 135° 중 가까운 것 — 15° 넘게 벗어나면 버린다(곡선 · 음영선은 여기서 빠진다).
  3 같은 방향 · 1.5 mm 안에서 이어지는 조각은 한 선으로 합친다. 합친 선 < 4 mm 는 버린다(적게).
  4 대칭: 몸통 · 머리 · 다리(좌우 짝)는 x 거울 선을 더한다. 팔(워그레이몬 · 가루몬)은 비대칭이라 안 한다.
  5 선은 부품을 가로질러 실루엣 안 1 mm 에서 끝난다(중간에서 끊긴 선은 긁힌 자국으로 읽혔다 — 09-26 첫 판).
    가로지른 길이의 25% 이상이 원화 근거여야 하고, 부품마다 근거 긴 순 3 줄(같은 방향 3 mm 안 평행선은 하나).
  6 홈 = 폭 0.8 · 보는 쪽 겉층 깊이 0.5 (부품 − 부품을 보는 방향 안으로 0.5 민 것). 벽이 보는 축과 나란한 면에는 안 판다.
정면 선은 앞 쪽 겉(작은 y)에, 뒤 선은 뒤 쪽 겉(큰 y)에 판다."""
import os, sys, json, time
import numpy as np, trimesh, manifold3d as M
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 디테일대조 as DD
from 메시출력 import 부채나누기

OUT = os.path.join(DD.D, "홈"); os.makedirs(OUT, exist_ok=True)
최소조각, 최소선, 각허용, 이음, 끝안, 폭, 깊, 근거비, 부품당선 = 3.0, 4.0, 15.0, 1.5, 1.0, 0.8, 0.5, 0.25, 3
안쪽 = {"정면": 1.0, "뒤": -1.0}
t_ = time.time()
def log(*a): print("[%4.0fs]" % (time.time() - t_), *a, flush=True)
def 대칭부품(n): return not n.startswith(("L팔끝", "R팔끝", "L손", "R손", "칼", "대포", "방패", "돌출", "L어깨", "R어깨", "L윗팔", "R윗팔"))

def 만폴드(tm):
    m = M.Manifold(M.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
    assert m.status() == M.Error.NoError, m.status()
    return m
def 메시(m):
    t = m.to_mesh(); return trimesh.Trimesh(np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts), process=False)

def 빠진선(보기, 부품):
    """디테일 대조와 같은 법으로 빠진 원화 패널 · 단차무늬 선분 (px 끝점)."""
    원 = DD.원화선(보기); 모 = DD.모델선(보기, 부품)
    dt모 = ndimage.distance_transform_edt(~np.any(list(모["종류"].values()), 0))
    rows, _ = DD.선분표(원["종류"], 보기, dt모)
    return [r for r in rows if r[0] in ("패널", "단차무늬") and r[3] < 0.5 and r[2] >= 최소조각]

def 규칙선(rows, 보기):
    """px 선분 → mm (x, z) 선분: 45° 맞춤 · 이어 붙이기 · 짧은 것 버림."""
    f, cx, r0, s, R, sg = DD.보기[보기]
    segs = []
    for r in rows:
        a, b = np.array(r[5][0], float), np.array(r[5][1], float)
        A_ = np.array([sg * (a[0] - cx) * s, (r0 - a[1]) * s]); B_ = np.array([sg * (b[0] - cx) * s, (r0 - b[1]) * s])
        d = B_ - A_; ang = np.degrees(np.arctan2(d[1], d[0])) % 180
        k = int(round(ang / 45.0)) % 4; 차 = abs(((ang - 45 * k) + 90) % 180 - 90)
        if 차 > 각허용: continue
        u = np.array([np.cos(np.radians(45 * k)), np.sin(np.radians(45 * k))]); c = (A_ + B_) / 2; L = abs(d @ u)
        segs.append([k, c - u * L / 2, c + u * L / 2])
    # 같은 방향 · 같은 줄(수직 거리 < 이음) · 끝 사이 < 이음 → 합침
    합쳐짐 = True
    while 합쳐짐:
        합쳐짐 = False
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                if segs[i][0] != segs[j][0]: continue
                k = segs[i][0]; u = np.array([np.cos(np.radians(45 * k)), np.sin(np.radians(45 * k))]); nrm = np.array([-u[1], u[0]])
                pi = [segs[i][1] @ u, segs[i][2] @ u]; pj = [segs[j][1] @ u, segs[j][2] @ u]
                if abs((segs[i][1] - segs[j][1]) @ nrm) > 이음 or max(pi[0], pj[0]) - min(pi[1], pj[1]) > 이음: continue
                off = ((segs[i][1] + segs[j][1]) / 2) @ nrm
                lo, hi = min(pi[0], pj[0]), max(pi[1], pj[1])
                segs[i] = [k, lo * u + off * nrm, hi * u + off * nrm]; segs.pop(j); 합쳐짐 = True; break
            if 합쳐짐: break
    return [(k, p, q) for k, p, q in segs if np.linalg.norm(q - p) >= 최소선]

def 판(cs, y0, y1): return cs.extrude(y1 - y0).transform(np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0]], float))

def main():
    부품 = DD.부품읽기(색분할=True, 돌출=True)
    결과 = {"설명": __doc__, "선": {}, "부품": {}}; 칼 = {}
    import 돌출 as DT; import importlib.util as IU
    _sp = IU.spec_from_file_location("색분할25", os.path.join(os.path.dirname(os.path.abspath(__file__)), "색분할.py"))
    C = IU.module_from_spec(_sp); _sp.loader.exec_module(C)
    for 보기 in ("정면", "뒤"):
        rows = 빠진선(보기, 부품); 선 = 규칙선(rows, 보기)
        앞, 이름들 = C.앞부품지도(보기, 부품); f, cx, r0, s, R, sg = DD.보기[보기]
        def 누구(p):
            u, v = int(round(sg * p[0] / s + cx)), int(round(r0 - p[1] / s))
            return 이름들[앞[v, u]] if 0 <= u < 1024 and 0 <= v < 1024 and 앞[v, u] >= 0 else None
        마스크 = {}
        def 부cs(n):
            if n not in 마스크:
                m부 = ndimage.binary_erosion(앞 == 이름들.index(n), iterations=max(1, int(round(끝안 / s))))
                마스크[n] = DT.격자단면(DT.격자로(m부, 보기)) if m부.any() else M.CrossSection()
            return 마스크[n]
        def 가로선(n, p, q):
            """선을 부품 실루엣(안 1 mm) 끝까지 늘려, 원래 선 가운데를 품는 조각 하나."""
            t = (q - p) / np.linalg.norm(q - p); w = np.array([-t[1], t[0]]) * 폭 / 2; c = (p + q) / 2
            띠 = M.CrossSection([np.array([c - 300 * t - w, c + 300 * t - w, c + 300 * t + w, c - 300 * t + w])]) ^ 부cs(n)
            점 = M.CrossSection([np.array([c - 0.2 * t - w * 0.5, c + 0.2 * t - w * 0.5, c + 0.2 * t + w * 0.5, c - 0.2 * t + w * 0.5])])
            for 조 in 띠.decompose():
                if not (조 ^ 점).is_empty(): return 조
            return None
        후보 = {}
        for k, p, q in 선:
            n = 누구((p + q) / 2)
            if n is None: continue
            조 = 가로선(n, p, q)
            if 조 is None: continue
            근거, 전체 = float(np.linalg.norm(q - p)), 조.area() / 폭
            if 전체 < 최소선 or 근거 / 전체 < 근거비: continue
            후보.setdefault(n, []).append(dict(k=k, p=p, q=q, 근거=근거, 전체=전체, cs=조))
        놓인 = []
        for n, L in 후보.items():   # 부품마다 근거 긴 순 · 같은 방향 3 mm 안 평행선은 하나 · 최대 부품당선
            L.sort(key=lambda d: -d["근거"]); 뽑 = []
            for d in L:
                u = np.array([np.cos(np.radians(45 * d["k"])), np.sin(np.radians(45 * d["k"]))]); nrm = np.array([-u[1], u[0]])
                if any(e["k"] == d["k"] and abs(((e["p"] + e["q"]) / 2 - (d["p"] + d["q"]) / 2) @ nrm) < 3.0 for e in 뽑): continue
                뽑.append(d)
                if len(뽑) >= 부품당선: break
            for d in 뽑:
                놓인.append((n, d))
                if 대칭부품(n):
                    pm, qm = d["p"] * [-1, 1], d["q"] * [-1, 1]; nm = 누구((pm + qm) / 2)
                    if nm is not None and 대칭부품(nm):
                        조 = 가로선(nm, pm, qm)
                        if 조 is not None and 조.area() / 폭 >= 최소선: 놓인.append((nm, dict(d, p=pm, q=qm, cs=조)))
        for n, d in 놓인:
            칼.setdefault((n, 보기), []).append(d["cs"])
            결과["선"].setdefault(보기, []).append(dict(부품=n, 원화근거mm=round(d["근거"], 1), 길이=round(d["전체"], 1), p=d["p"].round(2).tolist(), q=d["q"].round(2).tolist()))
        log(보기, "빠진 패널·단차 선분", len(rows), "→ 규칙 선", len(선), "→ 놓인 선(대칭 포함)", len(결과["선"].get(보기, [])))
    # 부품마다 파기
    파인 = {}
    for (n, 보기), css in 칼.items():
        if n not in 파인: 파인[n] = 만폴드(부품[n][0])
        m = 파인[n]; d = 안쪽[보기]
        O = m - m.translate([0.011, d * 깊, 0.017])                 # 보는 쪽 겉층 깊이 0.5
        홈 = M.Manifold.batch_boolean([판(c, -150.0, 150.0) for c in css], M.OpType.Add) ^ O
        m = m - 홈; ps = [c for c in m.decompose() if abs(c.volume()) >= 0.05]     # 홈 가장자리 부피 0 부스러기 버림
        파인[n] = M.Manifold.batch_boolean(ps, M.OpType.Add) if ps else m
    for n, m in 파인.items():
        fn = os.path.join(OUT, n + ".stl"); 메시(m).export(fn); wt = trimesh.load(fn).is_watertight
        for 양 in (0.03, 0.06, 0.10):
            if wt: break
            부채나누기(m, 양).export(fn); wt = trimesh.load(fn).is_watertight
        결과["부품"][n] = dict(파일=n + ".stl", 색=list(map(float, 부품[n][1])), 닫힘=bool(wt), 조각=len(m.decompose()),
                             파낸mm3=round(만폴드(부품[n][0]).volume() - m.volume(), 1))
    결과["입력해시"] = DD.입력해시(DD.선행["홈"])
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("홈 판 부품 %d · 선 정면 %d 뒤 %d" % (len(파인), len(결과["선"].get("정면", [])), len(결과["선"].get("뒤", []))),
        {k: v for k, v in 결과["부품"].items() if not v["닫힘"] or v["조각"] > 1})

if __name__ == "__main__":
    main()
