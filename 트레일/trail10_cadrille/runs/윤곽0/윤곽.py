# -*- coding: utf-8 -*-
"""윤곽0 — 실물 부품 실루엣 다각형을 밀어서(윤곽판) · 세 방향을 교차해서 CadQuery 로 짓기 · 학습 없음
python runs/윤곽0/윤곽.py [시작 끝]"""
import os, sys, json, time, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 실물보기 import 실물보기
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; N = 256; EPS = 0.005; ARC = os.environ.get("ARC") == "1"   # 10-11 호 판: 테두리를 직선 + 원호로 (꺾은선만 쓰면 휜 면이 토막 면이 됨)
PL = {0: "YZ", 1: "XZ", 2: "XY"}

def 다각형들(sil):   # 실루엣 → [(외곽 점들, [구멍 점들…])] · 좌표 = (o0, o1) 단위 상자
    im = (sil > .5).astype(np.uint8) * 255
    cs, hi = cv2.findContours(im, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hi is None: return []
    u = lambda p: [((pt[0][1] + .5) / N * 1.1 - .05, (pt[0][0] + .5) / N * 1.1 - .05) for pt in p]   # (행 = o0, 열 = o1)
    simp = lambda c: cv2.approxPolyDP(c, EPS * cv2.arcLength(c, True), True)
    out = []
    for i, c in enumerate(cs):
        if hi[0][i][3] != -1 or cv2.contourArea(c) < 4: continue
        holes = []; j = hi[0][i][2]
        while j != -1:
            if cv2.contourArea(cs[j]) >= 4: holes.append(u(simp(cs[j])))
            j = hi[0][j][0]
        o = u(simp(c))
        if len(o) >= 3: out.append((o, [h for h in holes if len(h) >= 3]))
    return out

def _원(a, b, c):   # 세 점을 지나는 원 (중심, 반지름) · 한 줄이면 None
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-9: return None
    s = [p[0] ** 2 + p[1] ** 2 for p in (a, b, c)]
    o = np.array([(s[0] * (b[1] - c[1]) + s[1] * (c[1] - a[1]) + s[2] * (a[1] - b[1])) / d, (s[0] * (c[0] - b[0]) + s[1] * (a[0] - c[0]) + s[2] * (b[0] - a[0])) / d])
    return o, float(np.linalg.norm(np.asarray(a) - o))

def 토막(P, tol=1.2, rmax=None):
    """닫힌 화소 테두리 P(n×2) → [("L", p0, p1) | ("A", p0, 가운데, p1)] · 앞에서부터 직선과 원호 중 더 멀리 가는 쪽으로 늘림 · 둘 다 tol 화소 안
    ponytail: 탐욕 늘리기 O(n²) · 부품당 테두리 수천 점이면 충분"""
    n = len(P); rmax = rmax or 3 * N
    def 직선됨(i, j):
        a, b = P[i], P[j % n]; q = P[[k % n for k in range(i, j + 1)]]; v = b - a; L = np.linalg.norm(v)
        if L < 1e-9: return False
        return np.abs(np.cross(v, q - a)).max() / L <= tol
    def 호됨(i, j):   # 최소제곱 원(Kasa) · 세 점 원은 화소 계단에 흔들려 못 씀
        q = P[[k % n for k in range(i, j + 1)]]; A_ = np.c_[2 * q, np.ones(len(q))]; b_ = (q ** 2).sum(1)
        x = np.linalg.lstsq(A_, b_, rcond=None)[0]; o = x[:2]; r = float(np.sqrt(max(x[2] + o @ o, 0)))
        if r < 3 or r > rmax: return None
        return (o, r) if np.abs(np.linalg.norm(q - o, axis=1) - r).max() <= tol else None
    out, i = [], 0
    while i < n:
        jl = i + 1
        while jl + 1 <= n and 직선됨(i, jl + 1): jl += 1
        ja = i + 2
        while ja + 4 <= n and 호됨(i, ja + 4) is not None: ja += 4
        if ja - i > jl - i + 4 and ja - i >= 8 and (c := 호됨(i, ja)) is not None:   # 가운데점만 원 위로
            on = lambda p: c[0] + (p - c[0]) / max(np.linalg.norm(p - c[0]), 1e-9) * c[1]
            out.append(("A", P[i], on(P[((i + ja) // 2) % n]), P[ja % n])); i = ja   # 끝점은 그대로(이웃 토막과 이어짐)
        else: out.append(("L", P[i], P[jl % n])); i = jl
    return out

def 다각형들_호(sil):   # 다각형들 과 같은 꼴 · 점 대신 토막 목록
    im = (sil > .5).astype(np.uint8) * 255
    cs, hi = cv2.findContours(im, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hi is None: return []
    u = lambda p: ((p[1] + .5) / N * 1.1 - .05, (p[0] + .5) / N * 1.1 - .05)
    def 변(c):
        P = c[:, 0, :].astype(float)
        k0 = int(np.argmin(np.linalg.norm(P - cv2.approxPolyDP(c, EPS * cv2.arcLength(c, True), True)[0][0], axis=1)))   # 꼭짓점에서 시작(호가 시작점에서 안 끊기게)
        return [(t, *[u(p) for p in ps]) for t, *ps in 토막(np.roll(P, -k0, axis=0))]
    out = []
    for i, c in enumerate(cs):
        if hi[0][i][3] != -1 or cv2.contourArea(c) < 4: continue
        holes = []; j = hi[0][i][2]
        while j != -1:
            if cv2.contourArea(cs[j]) >= 20 and min(abs(cv2.pointPolygonTest(c, (float(p[0][0]), float(p[0][1])), True)) for p in cs[j]) > 2:   # 구멍은 꺾은선 · 렌더 틈(10 화소 · 바깥선에 붙음)은 버림 — 원호 바깥선과 엇갈려 OCC 솔리드가 깨짐(#4)
                q = [u(p[0]) for p in cv2.approxPolyDP(cs[j], EPS * cv2.arcLength(cs[j], True), True)]
                if len(q) >= 3: holes.append([("L", q[k], q[(k + 1) % len(q)]) for k in range(len(q))])
            j = hi[0][j][0]
        out.append((변(c), holes))
    return out

def _선(wp, 변들):   # 토막 목록 → 닫힌 선
    p0 = 변들[0][1]; wp = wp.moveTo(p0[0] * 100, p0[1] * 100)
    for t, *ps in 변들:
        e = ps[-1]
        wp = wp.threePointArc((ps[1][0] * 100, ps[1][1] * 100), (e[0] * 100, e[1] * 100)) if t == "A" else wp.lineTo(e[0] * 100, e[1] * 100)
    return wp.close()

def 판(ax, sil, arc=None):   # 한 방향 윤곽판(축 ax 로 밀기) · 100 배 크기
    import cadquery as cq
    solid = None; o = [k for k in range(3) if k != ax]
    if ARC if arc is None else arc:
        for outer, holes in 다각형들_호(sil):
            wp = cq.Workplane(PL[ax]); f = _선(wp, outer)
            for h in holes: f = _선(f, h)
            try: s = f.extrude(80, both=True)
            except Exception: s = _선(wp, outer).extrude(80, both=True)
            c = [0, 0, 0]; c[ax] = 50; s = s.translate(tuple(c)) if PL[ax] != "XZ" else s.translate((0, 50, 0))
            solid = s if solid is None else solid.union(s)
        꺾 = 판(ax, sil, False)   # 원호 판은 OCC isValid 가 같은 입력에도 들쭉날쭉 · 부피로만 봄(꺾은선 판과 3 % 안) · 틀린 불리언은 교차 단계에서 다시 잡음
        if solid is not None and abs(solid.val().Volume() / 꺾.val().Volume() - 1) < .03: return solid
        print("호 판 깨짐 → 꺾은선", ax, None if solid is None else (solid.val().isValid(), round(solid.val().Volume() / 꺾.val().Volume(), 3))); return 꺾   # 원호가 이웃 직선을 넘어 꼬이면 OCC 가 깨진 솔리드를 냄 · 불리언이 조용히 틀림
        solid = None
    for outer, holes in 다각형들(sil):
        def xy(p):   # 작업면 지역 좌표: YZ → (Y, Z) · XZ → (X, Z) · XY → (X, Y)
            return [(a * 100, b * 100) for a, b in p]
        wp = cq.Workplane(PL[ax]).workplane(offset=0)
        f = wp.polyline(xy(outer)).close()
        for h in holes: f = f.polyline(xy(h)).close()
        try: s = f.extrude(80, both=True)
        except Exception: s = wp.polyline(xy(outer)).close().extrude(80, both=True)
        c = [0, 0, 0]; c[ax] = 50; s = s.translate(tuple(c)) if PL[ax] != "XZ" else s.translate((0, 50, 0))
        solid = s if solid is None else solid.union(s)
    return solid

def 메시로(s):
    import cadquery as cq, tempfile
    p = os.path.join(tempfile.gettempdir(), "윤곽_%d.stl" % os.getpid()); cq.exporters.export(s, p, tolerance=0.05, angularTolerance=0.2)
    m = trimesh.load(p); m.apply_scale(1 / 50.0); m.apply_translation([-1, -1, -1]); return m   # 100 배 단위 상자 → [-1,1]

if __name__ == "__main__":
    from s0 import unit
    from 모양자 import 재기
    a_, b_ = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 36)
    부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
    O = os.path.join(H, "결과" + ("_호" if ARC else "")); os.makedirs(O, exist_ok=True)
    for i in range(a_, b_):
        if os.path.exists(os.path.join(O, "%02d.json" % i)) and os.path.exists(os.path.join(O, "%02d_교차.step" % i)): continue
        m = unit(trimesh.load(RR + 부품[i], force="mesh")); gt = m.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        S, _ = 실물보기(m, N); r = {"부품": 부품[i]}; 판들 = {}
        for ax in range(3):
            try: 판들[ax] = 판(ax, S[2 * ax]); pm = 메시로(판들[ax]); r["A%d" % ax] = 재기(pm, gt)["edge_f1"]
            except Exception as e: r["A%d" % ax] = 0.0; print("판 실패", i, ax, str(e)[:60])
        r["A"] = max(r["A0"], r["A1"], r["A2"])
        try:
            b = 판들[0].intersect(판들[1]).intersect(판들[2])
            if ARC:   # 불리언이 조용히 틀리는 것 막기: 꺾은선 바탕 부피와 10 % 넘게 다르면 꺾은선 바탕
                b0 = 판(0, S[0], False).intersect(판(1, S[2], False)).intersect(판(2, S[4], False))
                if not abs(b.val().Volume() / b0.val().Volume() - 1) < .1: print("호 교차 틀림 → 꺾은선", i); b = b0; r["호"] = 0
                else: r["호"] = 1
            pm = 메시로(b); rb = 재기(pm, gt); r["B"] = rb["edge_f1"]; r["B_iou"] = rb["iou"]; pm.export(os.path.join(O, "%02d_교차.stl" % i)); cq_ = __import__('cadquery'); cq_.exporters.export(b, os.path.join(O, '%02d_교차.step' % i))   # 10-09 윤곽1: 손 깎기 바탕
        except Exception as e: r["B"] = 0.0; print("교차 실패", i, str(e)[:60])
        json.dump(r, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False); print(i, 부품[i][-34:], "A %.2f B %.2f" % (r["A"], r["B"]), flush=True)
