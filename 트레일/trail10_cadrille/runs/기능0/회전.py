# -*- coding: utf-8 -*-
"""회전체 어휘 — 실루엣(선 그림 바깥선)만 보고 회전체를 알아보고 CAD 회전으로 짓는다 · 판정기준13 · 10-12
SET=시험|검증 python runs/기능0/회전.py 찾기 번호…   → 축 · 돌림 · 대칭 점수 출력
SET=시험|검증 python runs/기능0/회전.py 짓기 번호…   → B_회전[_검증]/NN.stl · json (걸린 부품만)"""
import os, sys, json, numpy as np, cv2
from 도구 import *
돌림문턱, 대칭문턱, 칸 = 0.9, 0.85, 2   # 판정기준13 에 얼림
O = os.path.join(H, "B_회전" + ("" if 세트 == "시험" else "_" + 세트))
def _축정보(S, a):   # a 방향 실루엣 A · 무게중심(행 · 열) · 행 ↔ o_a[0] · 열 ↔ o_a[1]
    A = S[2 * a] > .5; ys, xs = np.nonzero(A); return A, (ys.mean(), xs.mean()) if len(xs) else (None, None)
def _돌림(A, c):   # 2판: 볼록 껍질이 같은 넓이 원판과 얼마나 겹치나 — 날개 · 톱니 · 구멍은 봐준다(1판 30/45/60° 돌림은 터빈 날에 깨짐)
    cs, _ = cv2.findContours(A.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return 0.0
    h = np.zeros(A.shape, np.uint8); cv2.fillPoly(h, [cv2.convexHull(np.vstack(cs))], 1); ys, xs = np.nonzero(h); cy, cx = ys.mean(), xs.mean(); r = np.sqrt(len(xs) / np.pi)
    yy, xx = np.mgrid[:A.shape[0], :A.shape[1]]; D = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r; H_ = h > 0
    return float((H_ & D).sum() / max((H_ | D).sum(), 1))
def _반지름(S, a, b, 중심):   # b 방향 실루엣에서 축 a 를 따라 행마다 (왼 · 오른) 반지름 — 축 위치는 a 방향 실루엣의 무게중심
    B = S[2 * b] > .5; o = [j for j in range(3) if j != b]; c3 = [j for j in range(3) if j not in (a, b)][0]
    if o[0] != a: B = B.T   # 그림 행 ↔ o[0] · 열 ↔ o[1] → 행 = a 좌표 · 열 = c3 좌표로 맞춤
    oa = [j for j in range(3) if j != a]; cc = 중심[0] if oa[0] == c3 else 중심[1]
    r = {}
    for z in range(B.shape[0]):
        xs = np.nonzero(B[z])[0]
        if len(xs): r[z] = (cc - xs.min(), xs.max() - cc)
    return r
def 찾기(S):
    best = None
    for a in range(3):
        A, c = _축정보(S, a)
        if c[0] is None: continue
        돌 = _돌림(A, c); b1, b2 = [j for j in range(3) if j != a]; r1, r2 = _반지름(S, a, b1, c), _반지름(S, a, b2, c)
        zs = sorted(set(r1) | set(r2)); 허 = lambda z: max(칸, 0.03 * max(r1[z] + r2[z]))   # 2판: 반지름 3 % 까지 봐줌
        ok = [z for z in zs if z in r1 and z in r2 and abs(r1[z][0] - r1[z][1]) <= 허(z) and abs(r2[z][0] - r2[z][1]) <= 허(z) and abs(sum(r1[z]) - sum(r2[z])) <= 2 * 허(z)]
        대 = len(ok) / max(len(zs), 1); 점 = min(돌, 대)
        if best is None or 점 > best["점"]: best = {"축": a, "돌림": round(돌, 3), "대칭": round(대, 3), "점": 점, "중심": c, "r": {z: (sum(r1[z]) + sum(r2[z])) / 4 for z in zs if z in r1 and z in r2}}
    best["걸림"] = best["돌림"] >= 돌림문턱 and best["대칭"] >= 대칭문턱; return best
def 짓기(i, f):
    import cadquery as cq
    a = f["축"]; oa = [j for j in range(3) if j != a]; 중 = [0.0, 0.0, 0.0]; 중[oa[0]] = c(f["중심"][0]); 중[oa[1]] = c(f["중심"][1])
    zs = sorted(f["r"]); 줄 = [(zs[0], 0.0)] + [(z, f["r"][z]) for z in zs] + [(zs[-1], 0.0)]
    p = cv2.approxPolyDP(np.array([[r * 10, z * 10] for z, r in 줄], np.int32).reshape(-1, 1, 2), 8, False)[:, 0, :] / 10.0   # 0.8 칸 안으로 줄임 · 축 위 두 점은 남음
    e_r = [0, 0, 0]; e_r[oa[0]] = 1   # 반지름 방향(축에 수직 아무 방향)
    pts = []
    for r, z in p:
        q = list(중); q[a] = c(z); q[oa[0]] += r * 화; pts.append(V(*q))
    if 꼬임([list(t) for t in p]): raise ValueError("꼬인 윤곽")
    면 = cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)); 축0 = list(중); 축0[a] = -50; 축1 = list(중); 축1[a] = 150
    s = cq.Workplane().add(cq.Solid.revolve(면, 360, V(*축0), V(*축1)))
    A, _ = _축정보(실루엣(i), a); cy, cx = int(round(f["중심"][0])), int(round(f["중심"][1]))
    if not A[cy, cx]:   # 가운데가 비면 그 반지름으로 축 관통 구멍
        ys, xs = np.nonzero(A); rin = float(np.min(np.hypot(ys - f["중심"][0], xs - f["중심"][1]))) * 화
        s = s.cut(원기둥(a, tuple(중[j] for j in oa), rin, -50, 150))
    교 = 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2))
    try:
        t = s.intersect(교); return t if t.val().Volume() > .3 * s.val().Volume() else s
    except Exception: return s
if __name__ == "__main__":
    일, ids = sys.argv[1], [int(x) for x in sys.argv[2:]]
    for i in ids:
        f = 찾기(실루엣(i)); print(세트, i, "축", f["축"], "돌림", f["돌림"], "대칭", f["대칭"], "걸림" if f["걸림"] else "", flush=True)
        if 일 == "짓기" and f["걸림"]:
            from 윤곽 import 메시로
            os.makedirs(O, exist_ok=True); s = 짓기(i, f); 메시로(s).export(os.path.join(O, "%02d.stl" % i))
            json.dump({"축": f["축"], "돌림": f["돌림"], "대칭": f["대칭"]}, open(os.path.join(O, "%02d.json" % i), "w"))
