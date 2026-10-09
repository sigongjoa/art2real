# -*- coding: utf-8 -*-
"""윤곽0 — 실물 부품 실루엣 다각형을 밀어서(윤곽판) · 세 방향을 교차해서 CadQuery 로 짓기 · 학습 없음
python runs/윤곽0/윤곽.py [시작 끝]"""
import os, sys, json, time, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 실물보기 import 실물보기
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; N = 256; EPS = 0.005
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

def 판(ax, sil):   # 한 방향 윤곽판(축 ax 로 밀기) · 100 배 크기
    import cadquery as cq
    solid = None; o = [k for k in range(3) if k != ax]
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
    O = os.path.join(H, "결과"); os.makedirs(O, exist_ok=True)
    for i in range(a_, b_):
        if os.path.exists(os.path.join(O, "%02d.json" % i)): continue
        m = unit(trimesh.load(RR + 부품[i], force="mesh")); gt = m.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        S, _ = 실물보기(m, N); r = {"부품": 부품[i]}; 판들 = {}
        for ax in range(3):
            try: 판들[ax] = 판(ax, S[2 * ax]); pm = 메시로(판들[ax]); r["A%d" % ax] = 재기(pm, gt)["edge_f1"]
            except Exception as e: r["A%d" % ax] = 0.0; print("판 실패", i, ax, str(e)[:60])
        r["A"] = max(r["A0"], r["A1"], r["A2"])
        try:
            b = 판들[0].intersect(판들[1]).intersect(판들[2]); pm = 메시로(b); rb = 재기(pm, gt); r["B"] = rb["edge_f1"]; r["B_iou"] = rb["iou"]; pm.export(os.path.join(O, "%02d_교차.stl" % i))
        except Exception as e: r["B"] = 0.0; print("교차 실패", i, str(e)[:60])
        json.dump(r, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False); print(i, 부품[i][-34:], "A %.2f B %.2f" % (r["A"], r["B"]), flush=True)
