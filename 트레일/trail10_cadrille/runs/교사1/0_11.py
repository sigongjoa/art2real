import cadquery as cq
w = (cq.Workplane('XZ', origin=(0, 13.3, 0)).moveTo(-100, -60).threePointArc((-98.6, -63.4), (-95.2, -64.8)).lineTo(95.2, -64.8).threePointArc((98.6, -63.4), (100, -60))
     .lineTo(100, 51.5).lineTo(73.3, 51.5).lineTo(73.3, -34.5).threePointArc((71, -40.1), (65.4, -42.4)).lineTo(-65.4, -42.4).threePointArc((-71, -40.1), (-73.3, -34.5))
     .lineTo(-73.3, 51.5).lineTo(-100, 51.5).close())
r = w.extrude(26.6)
for s in (-1, 1):
    x0 = 73.3 if s > 0 else -100
    r = r.union(cq.Workplane('YZ', origin=(x0, 0, 51.5)).circle(13.3).extrude(26.7))

for s in (-1, 1):
    x0 = 73.3 if s > 0 else -100
    r = r.cut(cq.Workplane('YZ', origin=(x0 - 1, 0, 51.7)).circle(3.3).extrude(30))
for c in (5.4, 16.4, 27.4, 38.4, 49.4, 60.4):   # 안쪽 바닥 톱니 홈 (폭 3.2 · 깊이 0.9)
    for s in (-1, 1):
        r = r.cut(cq.Workplane('XY').box(3.2, 30, 1.8).translate((s * c, 0, -42.4)))
