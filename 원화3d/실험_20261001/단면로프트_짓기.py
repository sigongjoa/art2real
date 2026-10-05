# -*- coding: utf-8 -*-
"""단면 로프트 머리 짓기 (freecadcmd) — loft_sec.json 단면을 이어(ruled 아님 · 위아래 매끈 · 둘레는 24 면) 속 찬 머리 → 눈 창을 앞에서 눈 깊이까지 파냄
출력 스크래치/cad/loft_body.stl"""
import json, FreeCAD as App, Part, Mesh
from FreeCAD import Vector
D = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/cad/"
L = json.load(open(D + "loft_sec.json")); P = json.load(open(D + "eyewin.json", encoding="utf-8"))["왼"]
ws = []
for s in L[::-1]:   # 아래 → 위
    pts = [Vector(x, y, s["z"]) for x, y in s["pts"]]; ws.append(Part.makePolygon(pts + [pts[0]]))
body = Part.makeLoft(ws, True, True)   # L2: ruled — 매끈 로프트는 단면 사이에서 출렁였다
ey = float(open(D + "eye_y.txt").read())
for Q in (P, [[-x, z] for x, z in P][::-1]):
    f = Part.Face(Part.makePolygon([Vector(x, -400, z) for x, z in Q] + [Vector(Q[0][0], -400, Q[0][1])]))
    body = body.cut(f.extrude(Vector(0, 400 + ey + 4, 0)))
print("loft", body.isValid(), round(body.Volume))
m = Mesh.Mesh(); m.addFacets(body.tessellate(0.3)); m.write(D + "loft_body.stl")
