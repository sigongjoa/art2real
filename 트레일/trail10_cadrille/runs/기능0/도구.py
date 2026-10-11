# -*- coding: utf-8 -*-
"""기능0 도구 — 기능 짓기에 쓰는 낱말 · 숫자는 그림(256 실루엣 화소)에서 읽어 넘긴다 · 10-11"""
import os, sys, json, numpy as np, trimesh, cadquery as cq
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "윤곽0"), os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
os.environ["ARC"] = "2"
import 윤곽 as W
V = cq.Vector; 부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]
c = lambda p: ((p + .5) / 256 * 1.1 - .05) * 100   # 256 화소 → CAD (단위 상자 × 100)
c8 = lambda p: ((p + .5) / 128 * 1.1 - .05) * 100
화 = 1.1 / 256 * 100   # 화소 하나 길이
_S = {}
def 꼬임(q):   # 닫힌 2D 다각형의 변끼리 서로 건너는 곳 수 — 0 이어야 CAD 면이 된다
    n = len(q); o = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return sum(o(q[i], q[(i + 1) % n], q[j]) * o(q[i], q[(i + 1) % n], q[(j + 1) % n]) < 0 and o(q[j], q[(j + 1) % n], q[i]) * o(q[j], q[(j + 1) % n], q[(i + 1) % n]) < 0
               for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1))
def 다각기둥(pts, d_):   # 꼬인 윤곽은 OCC 불리언이 메모리를 끝없이 잡는다(10-11 PC 다운 두 번) → 짓기 전에 막는다
    ax = int(np.argmax(np.abs(d_))); q = [[p_[j] for j in range(3) if j != ax] for p_ in ((v.x, v.y, v.z) for v in pts)]
    if len(q) < 3 or 꼬임(q): raise ValueError("꼬인 윤곽")
    return cq.Workplane().add(cq.Solid.extrudeLinear(cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)), V(*d_)))
def 실루엣(i):
    if i not in _S:
        from 실물보기 import 실물보기
        from s0 import unit
        _S[i] = 실물보기(unit(trimesh.load(W.RR + str(부[i]), force="mesh")), W.N)[0]
    return _S[i]
def 상자(x0, x1, y0, y1, z0, z1): return cq.Workplane().add(cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0)))
def 돌출(i, ax):   # 그 축 방향 실루엣(직선 + 원호 · 모서리 끊기)을 밀어낸 판 · 축 ax: 0 X · 1 Y · 2 Z
    return W.판(ax, 실루엣(i)[2 * ax], True)
def 원기둥(ax, 중심, r, a, b):   # 축 ax 방향 · 중심 = 나머지 두 좌표(CAD) · a~b
    d = [0, 0, 0]; d[ax] = 1; p = list(중심); p.insert(ax, a)
    return cq.Workplane().add(cq.Solid.makeCylinder(r, b - a, V(*p), V(*d)))
def 구(중심, r): return cq.Workplane().add(cq.Solid.makeSphere(r, V(*중심), angleDegrees1=-90))

_X = {}
def 입력(i):   # 128 선 그림 입력(S · D) — 선 고리와 같은 것
    if i not in _X: _X[i] = np.load(os.path.join(R, "깊이학습", "시험.npz"))["X"][i].astype(np.float32)
    return _X[i]
def 포켓(i, k, r0, r1, c0, c1, 델타=.04):
    """k 방향 깊이 그림의 네모(128 화소 행 r0~r1 · 열 c0~c1) 안에서 면보다 델타 넘게 깊은 곳 = 홈 → 그 윤곽을 홈 바닥 깊이까지 판 자르개
    ponytail: 가장 큰 덩이 하나 · 바닥은 중앙값 하나(평평) · 비탈 바닥은 못 냄"""
    import cv2
    X = 입력(i); S, D = X[0][k] > .5, X[3][k]; ax = k // 2; o = [j for j in range(3) if j != ax]
    m = np.zeros_like(S); m[r0:r1, c0:c1] = True; m &= S; d = np.where(m, D, np.nan); 면 = np.nanpercentile(d, 5)
    깊 = (m & (D > 면 + 델타)).astype(np.uint8); n, lab = cv2.connectedComponents(깊)
    if n < 2: return None
    j = 1 + int(np.argmax([(lab == q).sum() for q in range(1, n)])); 덩 = (lab == j).astype(np.uint8)
    cs, _ = cv2.findContours(덩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.0, True)[:, 0, :]
    바닥 = float(np.median(D[덩 > 0])); a = (1 - 바닥) * 110 - 5 if k % 2 else 바닥 * 110 - 5; 끝 = 120.0 if k % 2 else -20.0
    pts = []
    for cc, rr in p:   # (열, 행) → (o0 = 행, o1 = 열)
        q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = a; pts.append(V(*q))
    d_ = [0, 0, 0]; d_[ax] = 끝 - a
    return 다각기둥(pts, d_)

def 홈들(i, 최소=150):
    """자동 찾기가 짚은 홈 중 큰 것만 → CAD 자르개 목록 [(이름, 자르개)] · 홈 = 실물 깊이 − 교차 깊이 덩이(시험 입력) · 평평한 바닥 다각형 돌출
    ponytail: 탐색 json 을 다시 읽어 덩이를 네모로 맞춤 · 겹치는 덩이는 첫 것"""
    import cv2
    from scipy import ndimage
    X = 입력(i); S, D, Dh = X[0] > .5, X[3], X[2]; r = json.load(open(os.path.join(H, "탐색", "시험_%02d.json" % i), encoding="utf-8")); out = []
    for s in r["순서"]:
        if s["기능"] == "구 빼기":
            o = np.array(s["중심"]); out.append(("구 빼기 %d" % s["쪽"], 구(tuple(((o / 128) * 1.1 - .05) * 100), s["R"] * 1.1 / 128 * 100))); continue
        if s["기능"] != "포켓" or s["넓이"] < 최소: continue
        k = s["쪽"]; ax = k // 2; o = [j for j in range(3) if j != ax]
        lab, _ = ndimage.label(S[k] & (D[k] - Dh[k] > 3 / 128)); r0, r1, c0, c1 = s["네모"]
        ids, cnt = np.unique(lab[r0:r1, c0:c1][lab[r0:r1, c0:c1] > 0], return_counts=True); 덩 = (lab == ids[np.argmax(cnt)]).astype(np.uint8)
        cs, _ = cv2.findContours(덩, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.5, True)[:, 0, :]
        a = (1 - s["바닥"]) * 110 - 5 if k % 2 else s["바닥"] * 110 - 5; 끝 = 120.0 if k % 2 else -20.0; pts = []
        for cc, rr in p:
            q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = a; pts.append(V(*q))
        d_ = [0, 0, 0]; d_[ax] = 끝 - a
        out.append(("포켓 %d · %d칸" % (k, s["넓이"]), 다각기둥(pts, d_)))
    return out
