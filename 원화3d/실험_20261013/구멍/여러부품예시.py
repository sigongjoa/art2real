# 로드맵 1 단계 흐름도용 — 부품 종류 6 가지 예시(CadQuery) · 10-13
import cadquery as cq
O = "G:/art2real/out/설명/구멍/"
W = cq.Workplane
예 = {
 "판구멍": W("XY").box(26, 18, 6).faces(">Z").workplane().pushPoints([(-8, 0), (0, 0), (8, 0)]).hole(4),
 "돌기": W("XY").box(20, 20, 8).faces(">Z").workplane().circle(4).extrude(8),
 "기역": W("XY").box(24, 14, 6).union(W("XY").box(6, 14, 18).translate((-9, 0, 6))),
 "홈": W("XY").box(24, 16, 10).faces(">Z").workplane().rect(14, 5).cutBlind(-5),
 "원기둥구멍": W("XY").circle(10).extrude(14).faces(">Z").workplane().hole(8),
 "계단": W("XY").box(24, 16, 6).union(W("XY").box(12, 16, 6).translate((-6, 0, 6))).faces(">Z").workplane().hole(4),
}
for k, s in 예.items(): cq.exporters.export(s, O + "r예_%s.stl" % k, tolerance=0.01, angularTolerance=0.05)
print(" ".join("예_" + k for k in 예))
