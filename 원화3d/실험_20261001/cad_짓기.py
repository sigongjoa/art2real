# -*- coding: utf-8 -*-
"""CAD 짓기 v1 — FreeCAD 솔리드 (freecadcmd cad_짓기.py) · 입력 = cad_값.py 의 JSON(스크래치 ASCII 경로로 복사).
투구 = 타원체 E − 안쪽 타원체(껍질 1.8) − 얼굴 구멍(정면 윤곽을 앞으로 돌출한 프리즘)
차양 = 차양 윤곽(오른쪽 + 거울) 프리즘 ∩ 투구 바깥 6 층(E +6 − E) → 투구 곡면에 붙음은 구성상
출력: STL · FCStd (스크래치/cad)"""
import json, FreeCAD as App, Part, Mesh
from FreeCAD import Vector, Matrix
D = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
V = json.load(open(D + "v1.json", encoding="utf-8")); E = V["E"]
def 타원체(da=0.0):
    s = Part.makeSphere(1.0); m = Matrix(); m.scale(E["a"] + da, E["f"] + da, E["c"] + da); s = s.transformGeometry(m); s.translate(Vector(0, E["y0"], E["zc"])); return s
겉 = 타원체(0); 속 = 타원체(-V["껍질"]); 투구 = 겉.cut(속)
def 프리즘(pts, y_from, y_to):
    w = Part.makePolygon([Vector(x, y_from, z) for x, z in pts] + [Vector(pts[0][0], y_from, pts[0][1])]); f = Part.Face(w)
    return f.extrude(Vector(0, y_to - y_from, 0))
for P in V["얼굴 구멍"]:
    투구 = 투구.cut(프리즘(P, E["y0"], -300))
층 = 타원체(V["차양 두께"]).cut(겉)
차양 = None
for P in V["차양 오른쪽"]:
    for sgn in (1, -1):
        Q = [[sgn * x, z] for x, z in P]
        if sgn < 0: Q = Q[::-1]
        p = 프리즘(Q, E["y0"], -300).common(층); 차양 = p if 차양 is None else 차양.fuse(p)
print("helmet", 투구.isValid(), round(투구.Volume), "visor", 차양.isValid(), round(차양.Volume))
for nm, sh in (("helmet", 투구), ("visor", 차양)):
    m = Mesh.Mesh(); m.addFacets(sh.tessellate(0.3)); m.write(D + nm + "_v1.stl")
doc = App.newDocument("omega_v1")
for nm, sh in (("Helmet", 투구), ("Visor", 차양)): doc.addObject("Part::Feature", nm).Shape = sh
doc.saveAs(D + "omega_head_v1.FCStd"); print("saved")
