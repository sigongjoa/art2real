# -*- coding: utf-8 -*-
"""기능0 C 판 — 큰 홈 빼고(판결12 범인) · 바탕 = 교차 | 회전 ∩ 교차 · 원기둥 구간 · 공 관절 · 선 고리 디테일 · 판정기준14 · 10-12
SET=시험|검증 python runs/기능0/짓기C.py <깊이모델 이름> 번호…  →  B_C[_검증]/NN.stl · json(순서)"""
import os, sys, json, numpy as np, cv2, torch
from 도구 import *
import 디테일 as DT, 회전 as RV
sys.path.insert(0, os.path.join(R, "깊이학습"))
from 학습 import 망
O = os.path.join(H, ("B_O" if os.environ.get("ORACLE") else "B_E" if os.environ.get("REFINE") else "B_D" if os.environ.get("FILTER") else "B_C") + ("" if 세트 == "시험" else "_" + 세트))   # FILTER=1 → D 판(거름망이 통과시킨 홈만)
def 홈칼(i, k, c, 바닥):   # 짓기B 와 같음 — 덩이 윤곽을 바닥 깊이부터 바깥까지 민 기둥(128 칸)
    ax = k // 2; o = [j for j in range(3) if j != ax]
    cs, _ = cv2.findContours(c.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.5, True)[:, 0, :]
    a = (1 - 바닥) * 110 - 5 if k % 2 else 바닥 * 110 - 5; 끝 = 120.0 if k % 2 else -20.0; pts = []
    for cc, rr in p:
        q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = a; pts.append(V(*q))
    d_ = [0, 0, 0]; d_[ax] = 끝 - a
    return 다각기둥(pts, d_)
def 테두리(M): M8 = M.astype(np.uint8); return cv2.distanceTransform((1 - (M8 - cv2.erode(M8, np.ones((3, 3), np.uint8)))).astype(np.uint8), cv2.DIST_L2, 3)
def 원들(M):   # 허프 원 + 둘레의 몇 % 가 실루엣 테두리 위인가 · (행, 열, 반지름, 덮임)
    c = cv2.HoughCircles(cv2.GaussianBlur(M.astype(np.uint8) * 255, (5, 5), 1.5), cv2.HOUGH_GRADIENT, dp=1.2, minDist=8, param1=100, param2=18, minRadius=6, maxRadius=110)
    if c is None: return []
    T = 테두리(M); t = np.linspace(0, 2 * np.pi, 72, endpoint=False); out = []
    덮 = lambda y, x, r: float((T[np.clip((y + r * np.sin(t)).astype(int), 0, M.shape[0] - 1), np.clip((x + r * np.cos(t)).astype(int), 0, M.shape[1] - 1)] <= 2).mean())
    for x, y, r in c[0]:   # 허프 반지름 · 중심이 몇 칸 어긋남 → ±6 · ±3 안에서 덮임 큰 것으로 다듬음
        out.append(max(((float(y + dy), float(x + dx), float(r + dr), 덮(y + dy, x + dx, r + dr)) for dr in range(-6, 7, 2) for dy in (-3, 0, 3) for dx in (-3, 0, 3)), key=lambda q: q[3]))
    return out
def 공찾기(S):   # 두 방향 원이 맞고(공유 좌표 4 칸 · 반지름 15 %) 나머지 방향엔 그 자리 원판이 실루엣 안에 꽉 참(≥ 95 %) — 목 방향에선 공이 몸통에 겹쳐 원이 안 보임
    v = []
    for a in range(3):
        o = [j for j in range(3) if j != a]; M = S[2 * a] > .5; gy, gx = np.mgrid[:M.shape[0], :M.shape[1]]
        속 = lambda y, x, r: M[(gy - y) ** 2 + (gx - x) ** 2 <= (r - 2) ** 2].mean() >= .95   # 원 안이 꽉 참 — 구멍 테두리(핀 구멍)를 공으로 보지 않음
        v.append([({o[0]: y, o[1]: x}, r) for y, x, r, d in 원들(M) if d >= .55 and 속(y, x, r)])   # 둘레 55 % (개발 판에서 40 → 55 · 핀 · 링크 끝 헛걸림)
    yy, xx = np.mgrid[:S.shape[1], :S.shape[2]]; out = []
    for a, b in ((0, 1), (0, 2), (1, 2)):
        
        for pa, ra in v[a]:
            for pb, rb in v[b]:
                shared = [j for j in pa if j in pb]
                if not shared or abs(pa[shared[0]] - pb[shared[0]]) > 4 or abs(ra - rb) > .15 * max(ra, rb): continue
                ctr = {**pa, **pb}; ctr[shared[0]] = (pa[shared[0]] + pb[shared[0]]) / 2; r = (ra + rb) / 2
                c3 = [j for j in range(3) if j not in (a, b)][0]; o = [j for j in range(3) if j != c3]; M = S[2 * c3] > .5
                D = (yy - ctr[o[0]]) ** 2 + (xx - ctr[o[1]]) ** 2 <= (r - 2) ** 2
                if D.sum() == 0 or M[D].mean() < .95: continue
                ctr = (ctr[0], ctr[1], ctr[2])
                if not any(np.linalg.norm(np.subtract(ctr, q[0])) < r for q in out): out.append((ctr, r, (a, b)))
    return out
def _토막(B, z, cc):   # 줄 z 에서 열 cc 를 품은 채운 토막의 (왼 · 오른) 반지름
    row = B[z]; c = int(round(cc))
    if not (0 <= c < len(row)) or not row[c]: return None
    l = c
    while l > 0 and row[l - 1]: l -= 1
    r_ = c
    while r_ < len(row) - 1 and row[r_ + 1]: r_ += 1
    return cc - l + .5, r_ - cc + .5
def 원기둥구간(S):   # (축, 중심(행 · 열), [(z0, z1, {z: r})]) 목록
    out = []
    for a in range(3):
        A = S[2 * a] > .5; oa = [j for j in range(3) if j != a]
        for cy, cx, R_, d in 원들(A):
            if d < .4: continue
            yy, xx = np.mgrid[:A.shape[0], :A.shape[1]]; sq = (abs(yy - cy) <= R_ + 2) & (abs(xx - cx) <= R_ + 2); 밖 = sq & ((yy - cy) ** 2 + (xx - cx) ** 2 > (R_ + 2) ** 2) & A
            if 밖.sum() > .02 * sq.sum(): continue   # 원 둘레 네모 모서리에 다른 돌기 → 정사각 막대 · 붙은 블록
            Bs = []
            for b in oa:
                B = S[2 * b] > .5; ob = [j for j in range(3) if j != b]; B = B if ob[0] == a else B.T; c3 = [j for j in range(3) if j not in (a, b)][0]
                Bs.append((B, cy if oa[0] == c3 else cx))
            런, 지금 = [], {}
            for z in range(Bs[0][0].shape[0]):
                t0, t1 = _토막(Bs[0][0], z, Bs[0][1]), _토막(Bs[1][0], z, Bs[1][1]); ok = False
                if t0 and t1:
                    허 = max(2, .03 * max(t0 + t1)); ok = abs(t0[0] - t0[1]) <= 허 and abs(t1[0] - t1[1]) <= 허 and abs(sum(t0) - sum(t1)) <= 2 * 허 and max(t0 + t1) <= R_ + 3
                if ok: 지금[z] = (sum(t0) + sum(t1)) / 4
                elif 지금:
                    if len(지금) >= 4: 런.append(지금)
                    지금 = {}
            if len(지금) >= 4: 런.append(지금)
            if 런: out.append((a, (cy, cx), 런))
    return out
def 깎기(s, cutter):
    n0, v0 = len(s.solids().vals()), s.val().Volume()
    try:
        t = s.cut(cutter)
        if len(t.solids().vals()) <= n0 and t.val().Volume() >= .7 * v0: return t, True
    except Exception: pass
    return s, False
def 공깎기(s, cc, rr, 두축):   # 교차 − (공을 감싼 상자 − 공 − 목 심지) · 목 심지 = 공에서 몸통 쪽 축으로 반지름 0.45 원기둥(안 남기면 공이 떨어져 나감 — 10-12 #34 #5 #13)
    박 = 상자(*[t for j in range(3) for t in (cc[j] - rr, cc[j] + rr)]); 밖 = s.cut(박); bb = 밖.val().Center() if 밖.solids().vals() else None
    if bb is None: return s, False
    d = np.array([bb.x, bb.y, bb.z]) - np.array(cc); k = int(np.argmax(np.abs(d))); a, b = (cc[k], cc[k] + rr * 1.05) if d[k] > 0 else (cc[k] - rr * 1.05, cc[k])
    심 = 원기둥(k, tuple(cc[j] for j in range(3) if j != k), .45 * rr, a, b)
    통 = [원기둥(a, tuple(cc[j] for j in range(3) if j != a), rr, -50, 150) for a in 두축]   # 원이 보인 두 방향 무한 원기둥 — 공 윤곽 안에 투영되는 것만 깎음(상자 안 몸통은 남김 · #5 공이 블록 위)
    칼 = 박.cut(구(tuple(cc), rr)).intersect(통[0]).intersect(통[1]).cut(심)
    n0, v0 = len(s.solids().vals()), s.val().Volume(); t = s.cut(칼)
    큰 = [x for x in t.solids().vals() if x.Volume() >= .01 * v0]   # 1 % 아래 부스러기는 버림
    if len(큰) > n0 or sum(x.Volume() for x in 큰) < .7 * v0: return s, False
    import cadquery as cq
    return cq.Workplane().add(cq.Compound.makeCompound(큰)) if len(큰) > 1 else cq.Workplane().add(큰[0]), True
def 회전기둥(a, 중, rs):   # {z: r(px)} → 그 구간 회전체(CAD)
    import cadquery as cq
    zs = sorted(rs); 줄 = [(zs[0] - .5, 0.0)] + [(z, rs[z]) for z in zs] + [(zs[-1] + .5, 0.0)]
    p = cv2.approxPolyDP(np.array([[r * 10, z * 10] for z, r in 줄], np.int32).reshape(-1, 1, 2), 8, False)[:, 0, :] / 10.0
    if 꼬임([list(t) for t in p]): raise ValueError("꼬인 윤곽")
    oa = [j for j in range(3) if j != a]; pts = []
    for r, z in p:
        q = list(중); q[a] = c(z); q[oa[0]] += r * 화; pts.append(V(*q))
    축0 = list(중); 축0[a] = -50; 축1 = list(중); 축1[a] = 150
    return cq.Workplane().add(cq.Solid.revolve(cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)), 360, V(*축0), V(*축1))), c(zs[0] - .5), c(zs[-1] + .5), max(rs.values()) * 화
if __name__ == "__main__":
    from 윤곽 import 메시로
    from 모양자 import 재기
    from s0 import unit
    이름 = sys.argv[1]; m = 망().cuda(); m.load_state_dict(torch.load(os.path.join(R, "깊이학습", 이름 + ".pt"))); m.eval(); os.makedirs(O, exist_ok=True)
    for i in [int(x) for x in sys.argv[2:]]:
        X = 입력(i); S = 실루엣(i)
        with torch.no_grad(): Z = m(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()
        교 = 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2)); s = 교; 순서 = ["교차"]; n0 = len(s.solids().vals())
        f = RV.찾기(S)
        if f["걸림"]:
            try: s = RV.짓기(i, f); 순서.append("회전 축 %d" % f["축"])
            except Exception as e: 순서.append("회전 실패")
        else:
            for a, (cy, cx), 런 in 원기둥구간(S):
                oa = [j for j in range(3) if j != a]; 중 = [0.0, 0.0, 0.0]; 중[oa[0]] = c(cy); 중[oa[1]] = c(cx)
                for rs in 런:
                    try:
                        rv, z0, z1, rmax = 회전기둥(a, 중, rs); lo = [중[j] - rmax - 화 for j in range(3)]; hi = [중[j] + rmax + 화 for j in range(3)]; lo[a], hi[a] = z0, z1
                        s, 됨 = 깎기(s, 상자(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]).cut(rv))
                        if 됨: 순서.append("원기둥 구간 축 %d · %d 줄" % (a, len(rs)))
                    except Exception: pass
        for ctr, r, 두축 in 공찾기(S):
            try:
                s, 됨 = 공깎기(s, [c(t) for t in ctr], r * 화, 두축)
                if 됨: 순서.append("공 R%.0f" % r)
            except Exception: pass
        if os.environ.get("ORACLE"):   # 판정기준18 A 천장: 정답 깊이로 판 홈(윤곽 · 바닥 모두 정답)
            from scipy import ndimage as ND
            for k in range(6):
                lab, nl = ND.label((X[0][k] > .5) & (X[3][k] - X[2][k] > 2 / 128))
                for j in range(1, nl + 1):
                    m_ = lab == j
                    if m_.sum() < 60: continue
                    try:
                        t = s.cut(홈칼(i, k, m_, float(np.median(X[3][k][m_]))))
                        if len(t.solids().vals()) <= n0 and t.val().Volume() >= .7 * s.val().Volume(): s = t; 순서.append("홈(정답) %d · %d칸" % (k, m_.sum()))
                    except Exception: pass
        if os.environ.get("FILTER"):   # 판정기준16: 학생 깊이 홈 후보 → 거름망2 통과만 판다
            import 거름망 as GM
            hs = GM.후보들(X, Z); 통 = GM.고르기2([GM.조각(X, Z, k, m_) for k, m_, _ in hs], [f_ for _, _, f_ in hs]) if hs else []
            고른 = [h for h, ok in zip(hs, 통) if ok]
            if os.environ.get("REFINE"): 고른 = [(k, M, None) for k, M, _ in GM.다듬기(X, Z, 고른)]   # E 판(판정기준17): 배운 마스크 · 바닥 = 그 마스크 안 학생 깊이 중앙(바닥 보정은 못 배움)
            for k, m_, _ in 고른:
                try:
                    t = s.cut(홈칼(i, k, m_, float(np.median(Z[k][m_])))); 
                    if len(t.solids().vals()) <= n0 and t.val().Volume() >= .7 * s.val().Volume(): s = t; 순서.append("홈(거름망) %d · %d칸" % (k, m_.sum()))
                except Exception: pass
        if os.environ.get("DETAIL"): s, 디 = DT.얹기(s, DT.고리찾기(i, s, Z)); 순서 += ["%s %d" % (g["종"], g["쪽"]) for g in 디]   # 10-12 기본은 끔 — 선 고리 홈 · 보스도 #32 #22 를 긁음(큰 홈과 같은 병)
        gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(s); e = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i))
        json.dump({"부품": str(부[i]), "순서": 순서, "iou": e["iou"], "조각": len(s.solids().vals()) - n0}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, 순서[1:], flush=True)
