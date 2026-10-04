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
def 면XZ(pts, y): return Part.Face(Part.makePolygon([Vector(x, y, z) for x, z in pts] + [Vector(pts[0][0], y, pts[0][1])]))
def 면YZ(pts, x): return Part.Face(Part.makePolygon([Vector(x, y, z) for y, z in pts] + [Vector(x, pts[0][0], pts[0][1])]))
def 오프(pts, d):
    w = 면XZ(pts, 0).OuterWire.makeOffset2D(d, 0, False, False, False); return [[v.X, v.Z] for v in w.OrderedVertexes]
F0 = V4["정면 몸"] if VER >= 4 else V["정면 몸"]; S0 = V4["옆 몸"] if VER >= 4 else V["옆 몸"]
def 몸(d=0.0):
    F = 오프(F0, d) if d else F0; S = 오프(S0, d) if d else S0
    body = 면XZ(F, -400).extrude(Vector(0, 800, 0)).common(면YZ(S, -400).extrude(Vector(800, 0, 0)))
    xs = [p[0] for p in F]; ys = [p[0] for p in S]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; hx, hy = (x1 - x0) / 2, (y1 - y0) / 2; k = 0.3
    oc = [(cx - hx, cy - hy * (1 - k)), (cx - hx * (1 - k), cy - hy), (cx + hx * (1 - k), cy - hy), (cx + hx, cy - hy * (1 - k)), (cx + hx, cy + hy * (1 - k)), (cx + hx * (1 - k), cy + hy), (cx - hx * (1 - k), cy + hy), (cx - hx, cy + hy * (1 - k))]
    body = body.common(Part.Face(Part.makePolygon([Vector(x, y, -600) for x, y in oc] + [Vector(oc[0][0], oc[0][1], -600)])).extrude(Vector(0, 0, 800)))
    if VER >= 15:   # v15: 정수리 = 처마(L6) 위를 팔각 단면 4 장 ruled 로프트 돔으로(평평한 상자 위 대신)
        z6 = V4["층 z"]["L6 처마"]; zt = V4["꼭대기 z"] + 4 - d * 0
        body = body.cut(Part.makeBox(800, 800, 400, Vector(-400, -400, z6)))
        secs = []
        for s_, f_ in ((0.0, 1.0), (0.45, 0.88), (0.8, 0.6), (1.0, 0.25)):
            z = z6 + (zt - z6) * s_; pts = [Vector(cx + (x - cx) * f_, cy + (y - cy) * f_, z) for x, y in oc]; secs.append(Part.makePolygon(pts + [pts[0]]))
        body = body.fuse(Part.makeLoft(secs, True, True)).removeSplitter()
    return body
def 프리즘(pts, y_from, y_to): return 면XZ(pts, y_from).extrude(Vector(0, y_to - y_from, 0))
def 층(d): return 몸(d).cut(겉)
겉 = 몸(0); 속 = 몸(-V["껍질"]); 투구 = 겉.cut(속)
for P in V["얼굴 구멍"]: 투구 = 투구.cut(프리즘(P, E["y0"], -400))
부품 = {}
L6 = 층(8.0 if VER >= 20 else V["차양 두께"]); 차양 = None
for P in V["차양 오른쪽"]:
    for sgn in (1, -1):
        Q = [[sgn * x, z] for x, z in P]; Q = Q[::-1] if sgn < 0 else Q
        p = 프리즘(Q, E["y0"], -400).common(L6); 차양 = p if 차양 is None else 차양.fuse(p)
부품["visor"] = 차양
# 마스크
판들 = []
for i, P in enumerate(V["마스크 판"]):
    if len(P["윤곽"]) < 3: continue
    tip = P["앞 끝"] - ((6.0 if VER >= 18 else 3.0) * i if VER >= 5 else 0); hw = P["반폭"] * 1.05   # v18: 계단 6
    a = 프리즘(오프(P["윤곽"], -1.0) if VER >= 19 else P["윤곽"], 5, tip - 2)   # v19: 판 사이 틈 1
    W_ = Part.Face(Part.makePolygon([Vector(0, tip, -600), Vector(hw, 5, -600), Vector(-hw, 5, -600), Vector(0, tip, -600)])).extrude(Vector(0, 0, 800))
    pl = a.common(W_)
    if VER >= 5:   # 앞면에서 8 두께만 남김 = 판(속이 꽉 찬 쐐기 아님)
        W2 = Part.Face(Part.makePolygon([Vector(0, tip + 8, -600), Vector(hw, 5 + 8, -600), Vector(-hw, 5 + 8, -600), Vector(0, tip + 8, -600)])).extrude(Vector(0, 0, 800))
        pl = pl.cut(W2)
    판들.append(pl)
부품["mask"] = 판들[0].fuse(판들[1:]) if len(판들) > 1 else 판들[0]
if VER >= 6:
    SH = V4["뿔 옆"]
    if VER >= 14:   # v14: 옆 뿔 높이 범위를 정면 뿔 높이 범위에 끝끼리 맞춤(두 장 원근이 달라 겹침이 작았다)
        fz = [p[1] for p in V4["뿔 정면"]]; sz = [p[1] for p in SH]; a0, a1, b0, b1 = min(fz), max(fz), min(sz), max(sz)
        SH = [[y, a0 + (z - b0) * (a1 - a0) / max(1e-6, b1 - b0)] for y, z in SH]
    뿔 = 면XZ(V4["뿔 정면"], -400).extrude(Vector(0, 800, 0)).common(면YZ(SH, -400).extrude(Vector(800, 0, 0)))
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
        e = Part.makeCylinder(r, 2, Vector(cx, 0, cz), Vector(0, -1, 0)); eyes = e if eyes is None else eyes.fuse(e)
        ring = 프리즘(P, 1, -17.2).cut(프리즘(오프(P, -1.2), 1, -17.2)); walls = ring if walls is None else walls.fuse(ring)
        back = 프리즘(P, 3, 1); walls = walls.fuse(back)
    부품["eye"] = eyes; 부품["socket"] = walls
if VER >= 8:
    ants = None
    for p0, p1 in V4["안테나"]:
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); y_root = -20.0; a = Vector(p0[0], y_root, p0[1]); b = Vector(p1[0], y_root + L * math.tan(math.radians(30)), p1[1])
        c = Part.makeCone(2.4, 0.8, (b - a).Length, a, b - a); ants = c if ants is None else ants.fuse(c)
    부품["antenna"] = ants
if VER >= 9:
    L4 = 층(6.0 if VER >= 22 else 4.0); 볼 = None
    for P in V4["볼날개"]:
        p = 프리즘(P, E["y0"], -400).common(L4); 볼 = p if 볼 is None else 볼.fuse(p)
    부품["cheek"] = 볼
if VER >= 10:
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
if VER >= 13:
    위판 = None
    for P in V["차양 오른쪽"]:
        for sgn in (1, -1):
            Q = [[sgn * x, z + 2.0] for x, z in P]; Q = Q[::-1] if sgn < 0 else Q
            p = 프리즘(Q, E["y0"], -400).common(층(V["차양 두께"] + 3).cut(몸(V["차양 두께"]))); 위판 = p if 위판 is None else 위판.fuse(p)
    부품["visor2"] = 위판
if VER >= 21:   # v21: 돔 가운데 능선(뿔로 이어지는 띠) — 폭 8 프리즘 ∩ 바깥 2 층
    zz6 = V4["층 z"]["L6 처마"]; 띠 = Part.makeBox(8, 800, 200, Vector(-4, -400, zz6)).common(층(2.0)); 부품["ridge"] = 띠
부품["helmet"] = 투구
for nm, sh in 부품.items():
    if sh is None: continue
    m = Mesh.Mesh(); m.addFacets(sh.tessellate(0.3)); m.write(D + f"{nm}_v{VER}.stl")
doc = App.newDocument(f"omega_v{VER}")
for nm, sh in 부품.items():
    if sh is not None: doc.addObject("Part::Feature", nm).Shape = sh
doc.saveAs(D + f"omega_head_v{VER}.FCStd"); print("VER", VER, {k: (round(v.Volume) if v is not None else None) for k, v in 부품.items()})
