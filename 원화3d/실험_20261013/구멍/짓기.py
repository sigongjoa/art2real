# 쇼츠 구멍 편 재료 1 — CadQuery 로 20 mm 정육면체에 지름 d 구멍 · STL (반지름 3 · 4 · 5 · 6 · 목표 5) · 10-13
import cadquery as cq, os
O = "G:/art2real/out/설명/구멍/"; os.makedirs(O, exist_ok=True)
for r in (3, 4, 5, 6):
    s = cq.Workplane("XY").box(20, 20, 20).faces(">Z").workplane().hole(2 * r)
    cq.exporters.export(s, O + "r%d.stl" % r, tolerance=0.01, angularTolerance=0.05); print(r, round(s.val().Volume(), 1))
