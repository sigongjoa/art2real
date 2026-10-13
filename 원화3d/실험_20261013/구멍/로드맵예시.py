# 로드맵 그림용 예시 형태(CadQuery) — 1 단계: 상자 + 구멍 둘 + 원기둥 돌기 · 3 단계: ㄱ자 브래킷 + 필렛 + 구멍 + 홈 + 돌기 · 10-13
import cadquery as cq
O = "G:/art2real/out/설명/구멍/"
a = cq.Workplane("XY").box(24, 16, 10).faces(">Z").workplane().pushPoints([(-6, 0), (6, 0)]).hole(5).faces(">Z").workplane().center(0, 0).circle(2.5).extrude(0.01)
a = cq.Workplane("XY").box(24, 16, 10).faces(">Z").workplane().pushPoints([(-7, -3), (7, -3)]).hole(4).faces(">Z").workplane().center(0, 4).circle(3).extrude(6)
cq.exporters.export(a, O + "r로드1.stl", tolerance=0.01, angularTolerance=0.05)
b = (cq.Workplane("XY").box(30, 18, 5).union(cq.Workplane("XY").box(5, 18, 20).translate((-12.5, 0, 7.5))).edges("|Y").fillet(1.5)
     .faces(">Z[-2]").workplane().pushPoints([(4, -4), (4, 4), (11, 0)]).hole(3.5)
     .faces("<X").workplane().center(0, 9).slot2D(10, 3, 0).cutThruAll()
     .faces(">Z").workplane().center(0, 0).circle(2.2).extrude(4))
cq.exporters.export(b, O + "r로드3.stl", tolerance=0.01, angularTolerance=0.05); print("ok")
