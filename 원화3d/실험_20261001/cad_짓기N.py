# -*- coding: utf-8 -*-
"""CAD 짓기 v4 ~ v13 (freecadcmd · 스크래치 ver.txt 의 번호) — 10-04 사용자 「CAD 쓴 거야? 버전을 10 단위로 · 아직 별로」.
판마다 하나씩 더한다(앞 판 것은 그대로):
  v4  몸 = v4 윤곽(뿔 돌기 위 자름 · 옆 eps 6) — 정면 ∩ 옆 ∩ 팔각
  v5  마스크 판 계단: 아래 판일수록 앞으로 3 · 판마다 두께 판(앞면에서 8 만 남김)
  v6  뿔 = 정면 뿔 윤곽 밀기 ∩ 옆 뿔 윤곽 밀기(같은 패턴)
  v7  눈: 눈 윤곽 프리즘을 투구에서 빼고 눈 깊이 0 에 파란 눈 원판 + 검은 창 벽(윤곽 링 깊이 17)
  v8  안테나 둘(뿌리 = 몸 겉 · 끝 = 뒤로 30°) 원뿔대
  v9  볼날개 = 볼날개 윤곽 프리즘 ∩ 몸 바깥 4 층
  v10 번개 = 번개 윤곽 프리즘 ∩ 몸 바깥 0.8 층
  v11 속(검정) = 몸을 4 줄인 것 − 얼굴 앞(마스크 뒤만)
  v12 목 구멍: 아래에서 위로 원기둥 빼기(투구 아래 열림)
  v13 차양 위에 단차 판(차양 윗변을 2 위로 · 두께 3)"""
import json, math, FreeCAD as App, Part, Mesh
from FreeCAD import Vector
D = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
VER = int(open(D + "ver.txt").read().strip())
V = json.load(open(D + "v3.json", encoding="utf-8")); E = V["E"]; V4 = V["v4"]
if VER >= 35:   # v35: 눈 창 = 원화 정면에서 잰 왼 창(장갑 아닌 곳 중 눈 점과 이어진 것) + 좌우 거울 — 오른 창은 그늘 장갑과 섞여 못 잼
    _L = json.load(open(D + "eyewin.json", encoding="utf-8"))["왼"]; V4["눈"] = [_L, [[-x, z] for x, z in _L][::-1]]
def 면XZ(pts, y): return Part.Face(Part.makePolygon([Vector(x, y, z) for x, z in pts] + [Vector(pts[0][0], y, pts[0][1])]))
def 면YZ(pts, x): return Part.Face(Part.makePolygon([Vector(x, y, z) for y, z in pts] + [Vector(x, pts[0][0], pts[0][1])]))
def 오프(pts, d):
    w = 면XZ(pts, 0).OuterWire.makeOffset2D(d, 0, False, False, False); return [[v.X, v.Z] for v in w.OrderedVertexes]
F0 = V4["정면 몸"] if VER >= 4 else V["정면 몸"]; S0 = V4["옆 몸"] if VER >= 4 else V["옆 몸"]
if VER == 47:   # (v47 만 · 뒷걸음이라 되돌림) v47: 처마 아래 정면 윤곽의 꺾임마다 옆머리에 긴 면 · 턱(v46 폭 제한은 효과 없음) → 처마 아래는 처마 양 끝 → 턱 끝 사다리꼴 · 위 돔은 그대로
    _z6 = V4["층 z"]["L6 처마"]; _up = [p for p in F0 if p[1] >= _z6]
    _zb = min(p[1] for p in F0); _low = [p for p in F0 if p[1] <= _zb + 12]; _hc = max(6.0, (max(p[0] for p in _low) - min(p[0] for p in _low)) / 2)
    _xs = [p[0] for p in F0 if abs(p[1] - _z6) < 6] or [p[0] for p in _up]
    _xl, _xr = min(_xs), max(_xs)
    _upr = sorted([p for p in _up], key=lambda p: (-(p[0] > 0), p[1]))
    import math as _mm
    _c = (sum(p[0] for p in _up) / len(_up), sum(p[1] for p in _up) / len(_up))
    F0 = sorted(_up + [[_xl, _z6], [_xr, _z6], [_hc, _zb], [-_hc, _zb]], key=lambda p: _mm.atan2(p[1] - _c[1], p[0] - _c[0]))
if VER == 42:   # (v42 만 · 뒷걸음이라 되돌림) v42: 정면 몸 윤곽의 오목한 홈(볼 · 가시 자리)이 앞뒤로 밀려 옆머리를 가로지르는 긴 턱이 됐다 → 몸은 볼록 껍질(볼 · 가시 · 차양은 이제 따로 짓는 부품)
    import numpy as _np
    _P = _np.array(F0); _h = Part.makePolygon([Vector(x, 0, z) for x, z in F0] + [Vector(F0[0][0], 0, F0[0][1])])
    def _hull(pts):
        pts = sorted(set(map(tuple, pts)))
        def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
        lo, up = [], []
        for p in pts:
            while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
            lo.append(p)
        for p in reversed(pts):
            while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
            up.append(p)
        return [list(p) for p in lo[:-1] + up[:-1]]
    F0 = _hull(F0)
def 몸(d=0.0):
    F = 오프(F0, d) if d else F0; S = 오프(S0, d) if d else S0
    body = 면XZ(F, -400).extrude(Vector(0, 800, 0)).common(면YZ(S, -400).extrude(Vector(800, 0, 0)))
    if VER == 49:   # (v49 만 · 효과 없음 · 되돌림) v49: 정면 윤곽 꺾임이 앞뒤로 밀려 옆머리에 가로 띠 → 정면 윤곽은 얼굴 앞(y < −30)만, 뒤는 볼록 껍질 윤곽
        def _hl(pts):
            pts = sorted(set(map(tuple, pts)))
            def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
            lo_, up_ = [], []
            for q in pts:
                while len(lo_) >= 2 and cr(lo_[-2], lo_[-1], q) <= 0: lo_.pop()
                lo_.append(q)
            for q in reversed(pts):
                while len(up_) >= 2 and cr(up_[-2], up_[-1], q) <= 0: up_.pop()
                up_.append(q)
            return [list(q) for q in lo_[:-1] + up_[:-1]]
        앞 = 면XZ(F, -400).extrude(Vector(0, 370, 0)); 뒤 = 면XZ(_hl(F), -30).extrude(Vector(0, 430, 0))
        body = 앞.fuse(뒤).common(면YZ(S, -400).extrude(Vector(800, 0, 0)))
    xs = [p[0] for p in F]; ys = [p[0] for p in S]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; hx, hy = (x1 - x0) / 2, (y1 - y0) / 2; k = 0.3
    oc = [(cx - hx, cy - hy * (1 - k)), (cx - hx * (1 - k), cy - hy), (cx + hx * (1 - k), cy - hy), (cx + hx, cy - hy * (1 - k)), (cx + hx, cy + hy * (1 - k)), (cx + hx * (1 - k), cy + hy), (cx - hx * (1 - k), cy + hy), (cx - hx, cy + hy * (1 - k))]
    body = body.common(Part.Face(Part.makePolygon([Vector(x, y, -600) for x, y in oc] + [Vector(oc[0][0], oc[0][1], -600)])).extrude(Vector(0, 0, 800)))
    if VER >= 15:   # v15: 정수리 = 처마(L6) 위를 팔각 단면 4 장 ruled 로프트 돔으로(평평한 상자 위 대신)
        z6 = V4["층 z"]["L6 처마"]; zt = V4["꼭대기 z"] + 4 - d * 0
        if VER >= 26:   # v26: 돔 밑 팔각이 처마 높이 몸 단면보다 넓어 모자 챙 → 밑 팔각 = 처마 높이 몸 단면의 상자(얇은 판과 교집합)
            bb = body.common(Part.makeBox(800, 800, 2, Vector(-400, -400, z6 - 1))).BoundBox
            cx, cy, hx, hy = (bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2, bb.XLength / 2, bb.YLength / 2
            oc = [(cx - hx, cy - hy * (1 - k)), (cx - hx * (1 - k), cy - hy), (cx + hx * (1 - k), cy - hy), (cx + hx, cy - hy * (1 - k)), (cx + hx, cy + hy * (1 - k)), (cx + hx * (1 - k), cy + hy), (cx - hx * (1 - k), cy + hy), (cx - hx, cy + hy * (1 - k))]
        body = body.cut(Part.makeBox(800, 800, 400, Vector(-400, -400, z6)))
        if VER >= 46:   # v46: 처마 아래 몸이 볼 날개 자리만큼 옆으로 불룩해 옆머리에 긴 턱 → 처마 아래 폭을 처마 폭(+d)으로 제한(볼 · 가시는 따로 짓는 부품)
            body = body.common(Part.makeBox(2 * hx, 800, 400, Vector(cx - hx, -400, z6 - 400)))
        secs = []
        if VER >= 50:   # v50: 돔 밑 팔각이 처마 높이 실제 몸 단면과 달라 머리를 두른 턱(옆 띠) → 그 단면 자체를 24 점으로 줄여 쌓음
            sec_ = body.slice(Vector(0, 0, 1), z6 - 0.01); w_ = max(sec_, key=lambda w: w.Length)
            P24 = w_.discretize(24); gx = sum(p.x for p in P24) / 24; gy = sum(p.y for p in P24) / 24
            for s_, f_ in ((0.0, 1.0), (0.45, 0.88), (0.8, 0.6), (1.0, 0.25)):
                z = z6 - 0.01 + (zt - z6) * s_; pts = [Vector(gx + (p.x - gx) * f_, gy + (p.y - gy) * f_, z) for p in P24]; secs.append(Part.makePolygon(pts + [pts[0]]))
            body = body.cut(Part.makeBox(800, 800, 400, Vector(-400, -400, z6 - 0.01))).fuse(Part.makeLoft(secs, True, True)).removeSplitter()
        else:
            for s_, f_ in ((0.0, 1.0), (0.45, 0.88), (0.8, 0.6), (1.0, 0.25)):
                z = z6 + (zt - z6) * s_; pts = [Vector(cx + (x - cx) * f_, cy + (y - cy) * f_, z) for x, y in oc]; secs.append(Part.makePolygon(pts + [pts[0]]))
            body = body.fuse(Part.makeLoft(secs, True, True)).removeSplitter()
    return body
def 프리즘(pts, y_from, y_to): return 면XZ(pts, y_from).extrude(Vector(0, y_to - y_from, 0))
def 층(d): return 몸(d).cut(겉)
겉 = 몸(0); 속 = 몸(-(4.7 if VER >= 48 else V["껍질"])); 투구 = 겉.cut(속)   # v48: 출력 두께(머리 60 mm · 1.6 mm)
for P in V["얼굴 구멍"]: 투구 = 투구.cut(프리즘(P, E["y0"], -400))
부품 = {}
def VL(t):   # v44: V 얼굴을 따르는 t 두께 층 = (몸(t) ∩ V(yk − t/cosθ)) − (겉 ∩ V(yk))
    import os as _os, math as _m
    th = _m.radians(float(open(D + "theta.txt").read()) if _os.path.exists(D + "theta.txt") else 45.0); k = _m.tan(th)
    def vp(yk): return Part.Face(Part.makePolygon([Vector(0, yk, -600), Vector(300, yk + 300 * k, -600), Vector(300, 600, -600), Vector(-300, 600, -600), Vector(-300, yk + 300 * k, -600), Vector(0, yk, -600)])).extrude(Vector(0, 0, 800))
    fp = None
    for FP in V["얼굴 구멍"]:
        q = 겉.common(프리즘(FP, E["y0"], -400)); fp = q if fp is None else fp.fuse(q)
    yk = fp.BoundBox.YMin
    return 몸(t).common(vp(yk - t / _m.cos(th))).cut(겉.common(vp(yk)))
L6 = (VL(8.0) if VER >= 44 else 층(8.0 if VER >= 20 else V["차양 두께"])); 차양 = None
for P in ([] if VER >= 36 else V["차양 오른쪽"]):   # v36: 옛 가로 차양 판(원화와 달리 눈 창 위를 가로로 덮음) 뺌 — v33 눈썹 날개만
    for sgn in (1, -1):
        Q = [[sgn * x, z] for x, z in P]; Q = Q[::-1] if sgn < 0 else Q
        p = 프리즘(Q, E["y0"], -400).common(L6); 차양 = p if 차양 is None else 차양.fuse(p)
if VER >= 33:   # v33: 차양 = 화난 눈썹 날개 둘 — 특징점 차양 V(가운데 아래) · 차양 날개 끝(바깥 위) · 눈구멍 바깥 · 눈구멍 안 으로 사각 판 ∩ 바깥 8 층
    fp = V4["특징점"]
    for sd in ("왼", "오른"):
        if f"차양 날개/{sd}" not in fp: continue
        Vv, Wt, Eo, Ei = fp["차양 V"], fp[f"차양 날개/{sd}"], fp[f"눈구멍 바깥/{sd}"], fp[f"눈구멍 안/{sd}"]
        quad = [Vv, Wt, [Eo[0], Eo[1] + 6], [Ei[0], Ei[1] + 6]]
        if (Wt[0] - Vv[0]) * ((quad[2][1] - Vv[1])) - (quad[2][0] - Vv[0]) * (Wt[1] - Vv[1]) < 0: quad = quad[::-1]
        p = 프리즘(quad, E["y0"], -400).common(L6); 차양 = p if 차양 is None else 차양.fuse(p)
부품["visor"] = 차양
# 마스크
판들 = []
for i, P in enumerate(V["마스크 판"]):
    if len(P["윤곽"]) < 3: continue
    tip = P["앞 끝"] - ((6.0 if VER >= 18 else 3.0) * i if VER >= 5 else 0); hw = P["반폭"] * 1.05   # v18: 계단 6
    a = 프리즘(오프(P["윤곽"], -1.0) if VER >= 19 else P["윤곽"], 5, tip - 2)   # v19: 판 사이 틈 1
    yb = tip + 25.0 if VER >= 31 else 5   # v31: 쐐기 밑을 앞 끝 + 25 로 — 판 앞면이 정면을 보게(뾰족해 옆을 봐 어두웠다)
    W_ = Part.Face(Part.makePolygon([Vector(0, tip, -600), Vector(hw, yb, -600), Vector(-hw, yb, -600), Vector(0, tip, -600)])).extrude(Vector(0, 0, 800))
    if VER >= 31: W_ = W_.fuse(Part.makeBox(2 * hw, 400, 800, Vector(-hw, yb, -600)))
    if VER >= 28:   # v28: 판 정면 모양 = 얼굴 구멍 ∩ 그 판 높이 띠(칸 묶음은 좁아 구멍을 못 채움) − 눈 윤곽
        위 = (V4["층 z"]["L5 눈"] if (VER >= 30 and i == 0) else P["위"])   # v30: 코판은 눈 높이(L5)부터 — 눈 사이가 비어 검은 속이 보였다
        띠 = Part.makeBox(800, 800, 위 - P["아래"] + 3, Vector(-400, -400, P["아래"] - 1.5))
        a = None
        for FP in V["얼굴 구멍"]:
            q = 프리즘(FP, 5, tip - 2).common(띠); a = q if a is None else a.fuse(q)
        for EP in V4["눈"]: a = a.cut(프리즘(EP, 40, -400))
    pl = a.common(W_)
    if VER >= 5:   # 앞면에서 8 두께만 남김 = 판(속이 꽉 찬 쐐기 아님)
        W2 = Part.Face(Part.makePolygon([Vector(0, tip + 8, -600), Vector(hw, yb + 8, -600), Vector(-hw, yb + 8, -600), Vector(0, tip + 8, -600)])).extrude(Vector(0, 0, 800))
        if VER >= 31: W2 = W2.fuse(Part.makeBox(2 * hw, 400, 800, Vector(-hw, yb + 8, -600)))
        pl = pl.cut(W2)
    판들.append(pl)
부품["mask"] = 판들[0].fuse(판들[1:]) if len(판들) > 1 else 판들[0]
if VER >= 6:
    SH = V4["뿔 옆"]
    if VER >= 14:   # v14: 옆 뿔 높이 범위를 정면 뿔 높이 범위에 끝끼리 맞춤(두 장 원근이 달라 겹침이 작았다)
        fz = [p[1] for p in V4["뿔 정면"]]; sz = [p[1] for p in SH]; a0, a1, b0, b1 = min(fz), max(fz), min(sz), max(sz)
        SH = [[y, a0 + (z - b0) * (a1 - a0) / max(1e-6, b1 - b0)] for y, z in SH]
    뿔 = 면XZ(V4["뿔 정면"], -400).extrude(Vector(0, 800, 0)).common(면YZ(SH, -400).extrude(Vector(800, 0, 0)))
    if VER >= 32:   # v32: 뿔이 가는 기둥 → 마름모 밑(정면 밑 폭 · 옆 밑 앞뒤) → 꼭짓점(정면 · 옆 뿔 꼭대기 점)으로 ruled 로프트 = 밑 넓은 삼각 · 앞으로 기욺
        fz = [p[1] for p in V4["뿔 정면"]]; z0, z1 = min(fz), max(fz); zb_ = z0 + 0.15 * (z1 - z0)
        bx = [p[0] for p in V4["뿔 정면"] if p[1] <= zb_]; w = max(6.0, (max(bx) - min(bx)) / 2) * 1.3
        by = [p[0] for p in SH if p[1] <= zb_ + 0.2 * (z1 - z0)]; yf_, yb_ = min(by), max(by)
        top = max(V4["뿔 정면"], key=lambda p: p[1]); ty = min(SH, key=lambda p: -p[1])[0]
        base = [Vector(0, yf_, z0), Vector(w, (yf_ + yb_) / 2, z0), Vector(0, yb_, z0), Vector(-w, (yf_ + yb_) / 2, z0)]
        tip = [Vector(top[0] + dx, ty + dy, z1) for dx, dy in ((0, -0.8), (0.8, 0), (0, 0.8), (-0.8, 0))]
        뿔 = Part.makeLoft([Part.makePolygon(base + [base[0]]), Part.makePolygon(tip + [tip[0]])], True, True)
    if VER >= 45:   # v45: 원화 3/4 의 뿔은 얼굴 앞에 붙은 넓은 지느러미 판(앞 밑동 = 눈 사이 능선 · 뒤 밑동 = 정수리 · 끝은 앞으로 기욺) — 모델은 앞뒤 17 짜리 가시였다
        zb6 = V4["층 z"]["L6 처마"]; fp_ = V4["특징점"]; zbrow = fp_["차양 V"][1]
        hit = Part.LineSegment(Vector(0, -400, zbrow + 8), Vector(0, 400, zbrow + 8)).toShape().common(겉); yF = min(v.Y for v in hit.Vertexes) + 2
        hitB = Part.LineSegment(Vector(0, -400, zb6 + 25), Vector(0, 400, zb6 + 25)).toShape().common(겉); yB = (min(v.Y for v in hitB.Vertexes) + max(v.Y for v in hitB.Vertexes)) / 2
        Fp = Vector(0, yF, zbrow + 8); Bp = Vector(0, yB, zb6 + 25); Lp = Vector(-w, (yF + yB) / 2, (Fp.z + Bp.z) / 2 + 6); Rp = Vector(w, Lp.y, Lp.z)
        Tp = Vector(top[0] * 0, ty, z1)
        tri = lambda a, b, c: Part.Face(Part.makePolygon([a, b, c, a]))
        뿔 = Part.Solid(Part.Shell([tri(Tp, Fp, Lp), tri(Tp, Lp, Bp), tri(Tp, Bp, Rp), tri(Tp, Rp, Fp), tri(Fp, Bp, Lp), tri(Fp, Rp, Bp)]))
        if 뿔.Volume < 0: 뿔.reverse()
        print("horn45", round(yF), round(yB), round(ty), round(z1), round(w))
    부품["horn"] = 뿔
if VER >= 7:
    eyes = None; walls = None
    for P in V4["눈"]:
        if VER >= 17:   # v17: 각진 마름모(원화: 바깥-위로 치켜 올라간 각진 눈구멍) — 다각형의 좌 · 우 · 위 · 아래 끝 넷
            xs_ = [p[0] for p in P]; zs_ = [p[1] for p in P]
            P = [P[xs_.index(min(xs_))], P[zs_.index(max(zs_))], P[xs_.index(max(xs_))], P[zs_.index(min(zs_))]]
        투구 = 투구.cut(프리즘(P, 40, -400))
        cx = sum(p[0] for p in P) / len(P); cz = sum(p[1] for p in P) / len(P)
        r = max(4.0, (0.42 if VER >= 16 else 0.33) * (max(p[0] for p in P) - min(p[0] for p in P)))   # v16: 눈 크게
        if VER >= 24:   # v24: 눈이 창 안 깊이 0(겉에서 약 80 뒤)이라 가려 안 보임 → 창 입구 = 그 자리 몸 겉(광선) · 눈 = 입구 + 17.2(잰 창 깊이)
            hit = Part.LineSegment(Vector(cx, -400, cz), Vector(cx, 400, cz)).toShape().common(겉)
            s0 = min(v.Y for v in hit.Vertexes) if hit.Vertexes else -40.0
            if VER >= 43:   # v43: 눈이 V 로 물러난 얼굴판보다 30 가까이 앞에 있었다(깊이를 V 전 몸에서 잼) → 입구 = V 판 앞면 yk + |x|·tanθ
                import os as _os, math as _m
                _th = _m.radians(float(open(D + "theta.txt").read()) if _os.path.exists(D + "theta.txt") else 45.0)
                _fp = None
                for FP in V["얼굴 구멍"]:
                    q = 겉.common(프리즘(FP, E["y0"], -400)); _fp = q if _fp is None else _fp.fuse(q)
                s0 = max(s0, _fp.BoundBox.YMin + abs(cx) * _m.tan(_th))
        else:
            s0 = -17.2
        if VER >= 25:   # v25: 눈알이 창을 꽉 채움 → 원화처럼 검은 창 안 둥근 눈: 반지름 = 창 높이의 0.32 · 납작 원판 대신 앞으로 볼록한 반구(깊이 반지름 × 0.6)
            r = max(3.0, 0.32 * (max(p[1] for p in P) - min(p[1] for p in P)))
            e = Part.makeSphere(r, Vector(cx, s0 + 17.2, cz)); m_ = App.Matrix(); m_.scale(1, 0.6, 1); e = e.transformGeometry(m_) if False else e
            e = e.common(Part.makeBox(4 * r, 2 * r, 4 * r, Vector(cx - 2 * r, s0 + 17.2 - 2 * r, cz - 2 * r)))
        else:
            e = Part.makeCylinder(r, 2, Vector(cx, s0 + 17.2, cz), Vector(0, -1, 0))
        eyes = e if eyes is None else eyes.fuse(e)
        ring = 프리즘(P, s0 + 18.2, s0).cut(프리즘(오프(P, -(3.5 if VER >= 48 else 1.2)), s0 + 18.2, s0)); walls = ring if walls is None else walls.fuse(ring)
        back = 프리즘(P, s0 + 20.2, s0 + 18.2); walls = walls.fuse(back)
    부품["eye"] = eyes; 부품["socket"] = walls
if VER >= 8:
    ants = None
    for p0, p1 in V4["안테나"]:
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); y_root = -20.0; a = Vector(p0[0], y_root, p0[1]); b = Vector(p1[0], y_root + L * math.tan(math.radians(30)), p1[1])
        c = Part.makeCylinder(2.92, (b - a).Length, a, b - a) if VER >= 48 else Part.makeCone(2.4, 0.8, (b - a).Length, a, b - a); ants = c if ants is None else ants.fuse(c)   # v48: Ø2 mm 막대
    부품["antenna"] = ants
if VER >= 9:
    L4 = VL(6.0) if VER >= 44 else 층(6.0 if VER >= 22 else 4.0); 볼 = None
    for P in V4["볼날개"]:
        p = 프리즘(P, (-10.0 if VER >= 27 else E["y0"]), -400).common(L4); 볼 = p if 볼 is None else 볼.fuse(p)   # v27: 볼날개 프리즘이 머리 뒤까지 가 옆을 띠로 휘감음 → 눈 깊이 앞(−10)까지만
    if VER >= 29:   # v29: 볼날개가 얼굴 구멍(눈 · 마스크 자리) 앞을 덮음 → 얼굴 구멍 프리즘을 빼 옆 날개만
        for FP in V["얼굴 구멍"]: 볼 = 볼.cut(프리즘(오프(FP, -3.0), 40, -400))
    부품["cheek"] = None if VER >= 53 else 볼   # v53: 옆에서 눈높이 긴 판 — 원화 옆엔 없음 · 정면 볼 끝은 가시가 맡음
if 10 <= VER < 48:   # v48: 번개(0.3 mm)는 도색
    L08 = 층(0.8); 번 = None
    for P in V4["번개"]:
        if len(P) < 3: continue
        p = 프리즘(P, E["y0"], -400).common(L08); 번 = p if 번 is None else 번.fuse(p)
    부품["bolt"] = 번
core = 몸(-4.0) if VER >= 11 else 속
if VER >= 11:
    for P in V["얼굴 구멍"]: core = core.cut(프리즘(오프(P, -2), -60, -400))
부품["core"] = core
if VER >= 12:
    zb = min(p[1] for p in F0); neck = Part.makeCylinder(0.38 * (max(p[0] for p in F0) - min(p[0] for p in F0)), 30, Vector(0, E["y0"] + 20, zb - 1), Vector(0, 0, 1))
    투구 = 투구.cut(neck); 부품["core"] = 부품["core"].cut(neck)
if 13 <= VER < 36:
    위판 = None
    for P in V["차양 오른쪽"]:
        for sgn in (1, -1):
            Q = [[sgn * x, z + 2.0] for x, z in P]; Q = Q[::-1] if sgn < 0 else Q
            p = 프리즘(Q, E["y0"], -400).common(층(V["차양 두께"] + 3).cut(몸(V["차양 두께"]))); 위판 = p if 위판 is None else 위판.fuse(p)
    부품["visor2"] = 위판
if 21 <= VER < 48:   # v48: 능선(0.7 mm)은 도색 · v21: 돔 가운데 능선(뿔로 이어지는 띠) — 폭 8 프리즘 ∩ 바깥 2 층
    zz6 = V4["층 z"]["L6 처마"]; 띠 = Part.makeBox(8, 800, 200, Vector(-4, -400, zz6)).common(층(2.0)); 부품["ridge"] = 띠
if VER >= 34:   # v34: 원화 얼굴은 밝은 장갑판 + 검은 눈 창 둘 — 모델은 얼굴 전체가 검은 구멍 → 얼굴 구멍 자리 겉 껍질을 3 들여 다시 막고 눈 창만 뚫음
    판 = None
    for FP in V["얼굴 구멍"]:
        q = 겉.cut(몸(-3.0)).common(프리즘(FP, E["y0"], -400)); 판 = q if 판 is None else 판.fuse(q)
    판.translate(Vector(0, 3.0, 0))
    for EP in V4["눈"]: 판 = 판.cut(프리즘(오프(EP, 1.5), 60, -400))
    if VER >= 39:   # v39: 조사(research_메카얼굴단면) 레시피 A — V 를 판보다 먼저: 판 = (겉 ∩ 얼굴 구멍 ∩ V(yk, θ)) − V(yk + t/cosθ, θ) · 앞 · 뒷면이 같이 V → 두께 유지
        import os as _os, math as _m
        th = _m.radians(float(open(D + "theta.txt").read()) if _os.path.exists(D + "theta.txt") else 45.0)
        def vprism(yk):
            k = _m.tan(th); return Part.Face(Part.makePolygon([Vector(0, yk, -600), Vector(300, yk + 300 * k, -600), Vector(300, 600, -600), Vector(-300, 600, -600), Vector(-300, yk + 300 * k, -600), Vector(0, yk, -600)])).extrude(Vector(0, 0, 800))
        판 = None
        for FP in V["얼굴 구멍"]:
            q = 겉.common(프리즘(FP, E["y0"], -400)); 판 = q if 판 is None else 판.fuse(q)
        yk = 판.BoundBox.YMin
        _vback = vprism(yk + (4.7 if VER >= 48 else 3.0) / _m.cos(th)); 판 = 판.common(vprism(yk)).cut(_vback)
        if VER >= 52:   # v52: 얼굴 구멍이 옆벽을 y 7.5 까지 통째로 잘라 V 판 뒤가 비고 옆에 긴 턱 → V 판 뒤쪽의 투구 벽(겉 − 속)을 되살림 · 눈 창은 다시 뚫음
            re_ = None
            for FP in V["얼굴 구멍"]:
                q = 겉.cut(속).common(프리즘(FP, E["y0"], -400)).common(_vback); re_ = q if re_ is None else re_.fuse(q)
            for EP in V4["눈"]: re_ = re_.cut(프리즘(오프(EP, 1.5), 60, -400))
            투구 = 투구.fuse(re_)
        if VER >= 40: 부품["core"] = 부품["core"].common(_vback)   # v40: 속이 V 로 물러난 판보다 앞으로 나와 눈 옆이 검었다 → 속도 판 뒷면 V 로(갑주 ∩ 소체 = 0)
        for EP in V4["눈"]: 판 = 판.cut(프리즘(오프(EP, 1.5), 60, -400))
    elif VER >= 38:   # v38: 얼굴판을 위에서 본 V 로 — 가운데가 가장 앞, 옆으로 |x| × 0.7 물러남(원화: 가운데 능선 · 왼 밝고 오른 어둠)
        yf = 판.BoundBox.YMin
        판 = 판.common(Part.Face(Part.makePolygon([Vector(0, yf - 1, -600), Vector(200, yf - 1 + 140, -600), Vector(200, 400, -600), Vector(-200, 400, -600), Vector(-200, yf - 1 + 140, -600), Vector(0, yf - 1, -600)])).extrude(Vector(0, 0, 800)))
    부품["faceplate"] = 판
if 37 <= VER < 38:   # v37: 원화의 V 코판(눈 사이 → 아래 꼭짓점 · 가운데 능선) — 윤곽(자료/cad_코판.json) 기둥 ∩ 위에서 본 V(가운데 앞) ∩ 옆 사선(눈 사이 −30 → 아래 −92, 옆 축 코 −92)
    NP = json.load(open(D + "nosepoly.json"))
    zt_, zb_ = max(p[1] for p in NP), min(p[1] for p in NP); hw_ = max(abs(p[0]) for p in NP) + 2
    a = 프리즘(NP, 10, -120)
    topV = Part.Face(Part.makePolygon([Vector(0, -95, -600), Vector(hw_, -12, -600), Vector(hw_, 20, -600), Vector(-hw_, 20, -600), Vector(-hw_, -12, -600), Vector(0, -95, -600)])).extrude(Vector(0, 0, 800))
    side = 면YZ([[-30, zt_ + 6], [-30, zt_], [-95, zb_], [-95, zb_ - 20], [20, zb_ - 20], [20, zt_ + 6]], -400).extrude(Vector(800, 0, 0))
    부품["nose"] = a.common(topV).common(side)
if VER >= 41:   # v41: 원화 정면 볼 가시(옆판 아래 귀퉁이가 바깥-아래로 뾰족) — 삼각 (−98,−217)(−68,−190)(−58,−230) · 뿌리는 얼굴 앞(y −40~+10), 끝은 뒤(y +10~+40)로 뻗는 ruled 로프트 · 좌우 거울
    T = [(-98, -217), (-68, -190), (-58, -230)]; sp = None
    for sg in (1, -1):
        yb0, yb1, yt0, yt1 = (-45, -20, -32, -22) if VER >= 51 else (-40, 10, 10, 40)   # v51: 옆에서 긴 판으로 보여 깊이를 얼굴 옆으로 짧게
        root = [Vector(sg * T[1][0], yb0, T[1][1]), Vector(sg * T[2][0], yb0, T[2][1]), Vector(sg * T[2][0], yb1, T[2][1]), Vector(sg * T[1][0], yb1, T[1][1])]
        tipw = [Vector(sg * T[0][0], yt0, T[0][1] + 3), Vector(sg * T[0][0], yt0, T[0][1] - 3), Vector(sg * T[0][0], yt1, T[0][1] - 3), Vector(sg * T[0][0], yt1, T[0][1] + 3)]
        w = Part.makeLoft([Part.makePolygon(root + [root[0]]), Part.makePolygon(tipw + [tipw[0]])], True, True)
        sp = w if sp is None else sp.fuse(w)
    부품["spike"] = sp
부품["helmet"] = 투구
for nm, sh in 부품.items():
    if sh is None: continue
    m = Mesh.Mesh(); m.addFacets(sh.tessellate(0.3)); m.write(D + f"{nm}_v{VER}.stl")
m_ = Mesh.Mesh(); m_.addFacets(겉.tessellate(0.3)); m_.write(D + f"body_v{VER}.stl")   # 10-05: 속 찬 몸(머리 솔리드 바탕용)
if VER >= 48:   # v48: 출력용 한 솔리드(부품 전부 합침 · 눈알 포함 — 색은 도색)
    sol = None
    for nm_, sh_ in 부품.items():
        if sh_ is None: continue
        sol = sh_ if sol is None else sol.fuse(sh_)
    sol = sol.removeSplitter(); print("solid", sol.isValid(), len(sol.Solids), round(sol.Volume))
    m_ = Mesh.Mesh(); m_.addFacets(sol.tessellate(0.2)); m_.write(D + f"solid_v{VER}.stl")
doc = App.newDocument(f"omega_v{VER}")
for nm, sh in 부품.items():
    if sh is not None: doc.addObject("Part::Feature", nm).Shape = sh
doc.saveAs(D + f"omega_head_v{VER}.FCStd"); print("VER", VER, {k: (round(v.Volume) if v is not None else None) for k, v in 부품.items()})
