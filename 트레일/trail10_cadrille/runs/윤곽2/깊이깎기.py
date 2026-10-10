# -*- coding: utf-8 -*-
"""윤곽2 — 바탕(윤곽 교차 STEP) 위에 6 방향 깊이 차이로 주머니를 찾아 깎기 · 학습 없음
python runs/윤곽2/깊이깎기.py [시작 끝]"""
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 실물보기 import 실물보기
from 윤곽 import PL, 메시로
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; N = 256; TH = 0.02; MINA = int(os.environ.get("MINA", 40)); FLAT = float(os.environ.get("FLAT", 0))
TILT = float(os.environ.get("TILT", 0.02))   # 10-10 기울기 바닥: 영역 안 실물 깊이에 평면을 맞춰 잔차(세계 좌표 RMS) ≤ TILT 면 기울어진 바닥으로 깎음

def 주머니(Dr, Dh, Sr, Q=None, QK=0):   # Q = 확신 지도(잔차/퍼짐) · 주어지면 영역 중앙값 < QK 인 주머니는 통째로 안 깎음(10-10 2 판)   # 한 방향: 실물이 바탕보다 깊은 곳 → [(윤곽 점들(o0,o1), 깊이 d(격자 비율))]
    diff = ((Dr - Dh) > TH) & (Sr > .5)
    im = cv2.morphologyEx(diff.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(im, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); out = []
    for c in cs:
        if cv2.contourArea(c) < MINA: continue
        mk = np.zeros_like(im); cv2.drawContours(mk, [c], -1, 255, -1); d = float(np.median(Dr[mk > 0]))
        if Q is not None and float(np.median(Q[mk > 0])) < QK: continue
        pl = None
        if TILT:   # 깊이 d → 축 좌표는 d 의 일차식이라 d 에 평면을 맞추면 세계 좌표에도 평면
            yy, xx = np.nonzero(mk); A = np.c_[(yy + .5) / N * 1.1 - .05, (xx + .5) / N * 1.1 - .05, np.ones(len(yy))]
            co, *_ = np.linalg.lstsq(A, Dr[yy, xx], rcond=None); rms = float(np.sqrt(np.mean((A @ co - Dr[yy, xx]) ** 2))) * 1.1
            if rms <= TILT and np.abs(co[:2]).max() < 2.5: pl = co
            if pl is not None:   # 10-10 #18 이 0.70 → 0.17: 평면을 영역 꼭짓점까지 늘이면 실물 깊이 범위 밖으로 파고듦 → 범위 안일 때만
                v = Dr[mk > 0]; cv_ = c[:, 0, :]; pv = co[0] * ((cv_[:, 1] + .5) / N * 1.1 - .05) + co[1] * ((cv_[:, 0] + .5) / N * 1.1 - .05) + co[2]
                if pv.min() < np.percentile(v, 2) - .01 or pv.max() > np.percentile(v, 98) + .01: pl = None
        if FLAT:   # 10-10: 곡면을 주머니로 읽어 부스러기를 깎던 것 — 바닥 깊이가 고르지 않으면(10~90 % 폭 > FLAT) 안 깎음
            v = Dr[mk > 0]
            if np.percentile(v, 90) - np.percentile(v, 10) > FLAT: continue
        a = cv2.approxPolyDP(c, 0.005 * cv2.arcLength(c, True), True)
        pts = [((p[0][1] + .5) / N * 1.1 - .05, (p[0][0] + .5) / N * 1.1 - .05) for p in a]
        if len(pts) >= 3: out.append((pts, d, pl))
    return out

VMIN = float(os.environ.get("VMIN", 0.85)); 기록 = []
def 기울기둥(ax, fl, pts, a, b, c0):
    """깊이 평면 d = a·u + b·v + c0 (u, v = 남은 두 축 세계 좌표) 를 바닥으로 하는 깎기 기둥(×100 단위 · 이미 제자리)"""
    import cadquery as cq
    w = lambda u, v: ((a * u + b * v + c0) if not fl else (1 - (a * u + b * v + c0))) * 1.1 - .05   # 표면 세계 좌표
    ws = [w(u, v) for u, v in pts]
    lo, hi = (-0.2, max(ws) + .01) if not fl else (min(ws) - .01, 1.2)
    s_ = cq.Workplane(PL[ax]).polyline([(p * 100, q * 100) for p, q in pts]).close().extrude((hi - lo) * 100)
    bb = s_.val().BoundingBox(); off = [0, 0, 0]; off[ax] = lo * 100 - (bb.xmin, bb.ymin, bb.zmin)[ax]; s_ = s_.translate(tuple(off))
    o = [k for k in range(3) if k != ax]; sg = 1 if not fl else -1   # 축 좌표 x = 1.1·(a u + b v + c0) − .05  (뒤집힌 쪽은 1 − …)
    nrm = [0.0, 0.0, 0.0]; nrm[ax] = 1.0; nrm[o[0]] = -1.1 * a * sg; nrm[o[1]] = -1.1 * b * sg
    P0 = [0.0, 0.0, 0.0]; P0[ax] = w(0, 0) * 100
    n_ = cq.Vector(*nrm).normalized(); xd = n_.cross(cq.Vector(*[1.0 if k == o[0] else 0.0 for k in range(3)]))
    if xd.Length < 1e-6: return None
    반 = cq.Workplane(cq.Plane(cq.Vector(*P0), xd.normalized(), n_)).rect(2000, 2000).extrude(-1000 if not fl else 1000)
    try: return s_.intersect(반)
    except Exception: return None
def 깎기(바탕, m_real, m_base, 검증=None, 보기r=None):   # 보기r = (Sr, Dr) 를 주면 실물 대신 그 깊이로(10-10 깊이학습 평가)
    import cadquery as cq
    Sr, Dr, *Qs = 보기r if 보기r is not None else 실물보기(m_real, N); Sh, Dh = 실물보기(m_base, N); r = 바탕; n = 0
    for ax in range(3):
        for fl in (False, True):
            k = 2 * ax + (1 if fl else 0)
            for pts, d, pl in 주머니(Dr[k], Dh[k], Sr[k], *((Qs[0][k], Qs[1]) if Qs else ())):
                # 실물보기 규약: 낮은 쪽에서 본 깊이 d → 표면 세계 좌표 w = d·1.1 − 0.05 · 높은 쪽에서 본 것 → w = (1 − d)·1.1 − 0.05
                if not fl: lo, hi = -0.2, d * 1.1 - .05
                else: lo, hi = (1 - d) * 1.1 - .05, 1.2
                try:   # 10-10 꼬인 윤곽(자기 교차)은 빈 기둥 → 건너뜀
                    s_ = cq.Workplane(PL[ax]).polyline([(a * 100, b * 100) for a, b in pts]).close().extrude((hi - lo) * 100)
                    bb = s_.val().BoundingBox(); mn = (bb.xmin, bb.ymin, bb.zmin)[ax]
                except Exception: continue
                off = [0, 0, 0]; off[ax] = lo * 100 - mn                     # 축 방향으로 [lo, hi] 에 오게(작업면 법선 방향과 상관없이)
                if pl is not None:   # 기울기 바닥: 기둥을 평면까지 넉넉히 뽑고 평면 반대쪽 반공간과 교차
                    a, b, c0 = pl
                    try: s_ = 기울기둥(ax, fl, pts, a, b, c0)
                    except Exception: s_ = None
                    if s_ is None: continue
                    off = [0, 0, 0]
                if 검증 is not None:   # 10-10 검증 깎기: 기둥 안 점이 실물에서도 비어 있어야 깎는다(곡면 겉을 홈으로 읽은 것을 거름)
                    bb2 = s_.translate(tuple(off)).val().BoundingBox(); rng = np.random.default_rng(0)
                    q = rng.uniform([bb2.xmin, bb2.ymin, bb2.zmin], [bb2.xmax, bb2.ymax, bb2.zmax], (4000, 3)) / 100.0
                    q = q[(q >= -0.02).all(1) & (q <= 1.02).all(1)]
                    o_ = [k for k in range(3) if k != ax]; pg = np.array(pts, np.float32).reshape(-1, 1, 2)
                    q = q[[cv2.pointPolygonTest(pg, (float(x[o_[0]]), float(x[o_[1]])), False) >= 0 for x in q]][:1500]
                    if len(q) < 30: continue
                    빈 = 1 - 검증(q).mean(); 기록.append((ax, fl, round(float(빈), 3)))
                    if 빈 < VMIN: continue
                try:   # 10-10 #18: 기울기둥 하나가 부피를 음수(−104881)로 뒤집음 → 결과 부피가 양수이고 줄었을 때만 받음
                    r2 = r.cut(s_.translate(tuple(off))); v0, v1 = r.val().Volume(), r2.val().Volume()
                    if 0 < v1 <= v0 + 1e-6: r = r2; n += 1
                except Exception: pass
    return r, n

if __name__ == "__main__":
    import cadquery as cq
    from s0 import unit
    from 모양자 import 재기
    a_, b_ = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 36)
    부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
    O = os.path.join(H, os.environ.get("OUTN", "결과")); os.makedirs(O, exist_ok=True)
    for i in range(a_, b_):
        sp = os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i)
        if not os.path.exists(sp): print(i, "바탕 없음"); continue
        m = unit(trimesh.load(RR + 부품[i], force="mesh")); gt = m.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        mb = trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)); mb.apply_translation([1, 1, 1]); mb.apply_scale(.5)   # [-1,1] → 단위 상자
        검증 = None
        if os.environ.get("VERIFY") == "1":
            from 모양자 import _occ
            검증 = lambda q, m=m: _occ(m, q)   # 단위 상자 좌표의 점 → 실물 안이면 참
        기록.clear(); 바탕 = cq.importers.importStep(sp); r, n = 깎기(바탕, m, mb, 검증)
        try: pm = 메시로(r); res = 재기(pm, gt); pm.export(os.path.join(O, "%02d_깎음.stl" % i))
        except Exception as e: res = {"edge_f1": 0.0, "iou": 0.0}; print("실패", i, str(e)[:60])
        base = json.load(open(os.path.join(R, "윤곽0", "결과", "%02d.json" % i), encoding="utf-8"))["B"]
        json.dump({"idx": i, "바탕": base, "edge_f1": res["edge_f1"], "iou": res["iou"], "깎은 수": n, "검증": list(기록)}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, 부품[i][-30:], "바탕 %.2f → 깎음 %.2f · %d 개" % (base, res["edge_f1"], n), flush=True)
