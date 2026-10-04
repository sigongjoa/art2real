# -*- coding: utf-8 -*-
"""CAD 짓기 v2 (freecadcmd) — 조사 패턴(claudedocs/research_CAD메카머리패턴_20261004.md):
  ② 두 방향 밀기의 교집합: 몸 = 정면 몸 윤곽(XZ)을 y 로 밀기 ∩ 옆 몸 윤곽(YZ)을 x 로 밀기 → 모서리가 각진 머리(공 아님)
  ③ 위에서 본 모양(평면)은 각진 팔각 기둥으로 한 번 더 깎음(ruled 깎은 면 — 옆머리 모서리를 45° 로 침)
  ⑭ 껍질 = 같은 연산을 1.8 줄인 윤곽으로 다시 지어 뺌(makeThickness 피함)
  얼굴 구멍 · 차양은 v1 과 같음(차양 층 = 몸을 6 키운 것 − 몸)
출력: helmet_v2.stl · visor_v2.stl · omega_head_v2.FCStd"""
import json, FreeCAD as App, Part, Mesh
from FreeCAD import Vector
D = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
V = json.load(open(D + "v1.json", encoding="utf-8")); E = V["E"]
def 면XZ(pts, y):
    return Part.Face(Part.makePolygon([Vector(x, y, z) for x, z in pts] + [Vector(pts[0][0], y, pts[0][1])]))
def 면YZ(pts, x):
    return Part.Face(Part.makePolygon([Vector(x, y, z) for y, z in pts] + [Vector(x, pts[0][0], pts[0][1])]))
def 줄임(pts, d):   # 2D 다각형을 d 만큼 안으로(OCCT 2D 오프셋)
    f = 면XZ(pts, 0); w = f.OuterWire.makeOffset2D(-d, 0, False, False, False)
    return [[v.X, v.Z] for v in w.OrderedVertexes]
def 몸(d=0.0):
    F = V["정면 몸"]; S = V["옆 몸"]
    if d: F = 줄임(F, d); S = [[p[0], p[1]] for p in [[q[0], q[1]] for q in 줄임([[y, z] for y, z in S], d)]]
    a = 면XZ(F, -400).extrude(Vector(0, 800, 0)); b = 면YZ(S, -400).extrude(Vector(800, 0, 0)); body = a.common(b)
    # 평면 팔각 — 위에서 본 머리: 좌우 반폭 = 정면 최대, 앞뒤 = 옆 최대, 네 귀를 25 % 침
    xs = [p[0] for p in F]; ys = [p[0] for p in S]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2; k = 0.3
    oc = [(cx - hx, cy - hy * (1 - k)), (cx - hx * (1 - k), cy - hy), (cx + hx * (1 - k), cy - hy), (cx + hx, cy - hy * (1 - k)),
          (cx + hx, cy + hy * (1 - k)), (cx + hx * (1 - k), cy + hy), (cx - hx * (1 - k), cy + hy), (cx - hx, cy + hy * (1 - k))]
    top = Part.Face(Part.makePolygon([Vector(x, y, -600) for x, y in oc] + [Vector(oc[0][0], oc[0][1], -600)])).extrude(Vector(0, 0, 800))
    return body.common(top)
겉 = 몸(0); 속 = 몸(V["껍질"]); 투구 = 겉.cut(속)
def 프리즘(pts, y_from, y_to):
    return 면XZ(pts, y_from).extrude(Vector(0, y_to - y_from, 0))
for P in V["얼굴 구멍"]: 투구 = 투구.cut(프리즘(P, E["y0"], -400))
층 = 겉.makeOffsetShape(V["차양 두께"], 0.1, join=2).cut(겉) if False else None
# 차양 층: 정면 · 옆 윤곽을 6 키워 다시 지은 몸 − 겉
def 키움(pts, d): return 줄임(pts, -d)
F6 = 키움(V["정면 몸"], V["차양 두께"]); S6 = [[y, z] for y, z in 키움([[y, z] for y, z in V["옆 몸"]], V["차양 두께"])]
큰 = 면XZ(F6, -400).extrude(Vector(0, 800, 0)).common(면YZ(S6, -400).extrude(Vector(800, 0, 0)))
층 = 큰.cut(겉)
차양 = None
for P in V["차양 오른쪽"]:
    for sgn in (1, -1):
        Q = [[sgn * x, z] for x, z in P]
        if sgn < 0: Q = Q[::-1]
        p = 프리즘(Q, E["y0"], -400).common(층); 차양 = p if 차양 is None else 차양.fuse(p)
print("helmet", 투구.isValid(), round(투구.Volume), "visor", 차양.isValid() if 차양 else None, round(차양.Volume) if 차양 else 0)
for nm, sh in (("helmet", 투구), ("visor", 차양), ("core", 속)):
    m = Mesh.Mesh(); m.addFacets(sh.tessellate(0.3)); m.write(D + nm + "_v2.stl")
doc = App.newDocument("omega_v2")
for nm, sh in (("Helmet", 투구), ("Visor", 차양)): doc.addObject("Part::Feature", nm).Shape = sh
doc.saveAs(D + "omega_head_v2.FCStd"); print("saved")
