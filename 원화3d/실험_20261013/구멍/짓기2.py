# 프레임 시안용 추가 형태 — 구멍 없는 상자(r0) · r1 · r2 · 엇나간 구멍(r4 · 옆으로 4 mm) · 10-13
import cadquery as cq
O = "G:/art2real/out/설명/구멍/"
cq.exporters.export(cq.Workplane("XY").box(20, 20, 20), O + "r0.stl")
for r in (1, 2): cq.exporters.export(cq.Workplane("XY").box(20, 20, 20).faces(">Z").workplane().hole(2 * r), O + "r%d.stl" % r, tolerance=0.01, angularTolerance=0.05)
cq.exporters.export(cq.Workplane("XY").box(20, 20, 20).faces(">Z").workplane().center(4, 0).hole(8), O + "r4엇.stl", tolerance=0.01, angularTolerance=0.05)
print("ok")
