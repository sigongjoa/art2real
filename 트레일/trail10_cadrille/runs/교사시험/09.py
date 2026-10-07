import cadquery as cq
# 모두 부품 좌표(기울기 전)에서 짓고 마지막에 Y 축으로 12.5° 돌린다
clip = cq.Workplane('XY').box(134.2, 100, 74.6).translate((0, -50, 0)).edges('|Z and <Y').fillet(20).edges('|Z and >Y').chamfer(7.5)
clip = clip.cut(cq.Workplane('XY').sphere(43.3).translate((0, -67, 0)))
clip = clip.cut(cq.Workplane('XZ', origin=(0, -90, 0)).circle(36.7).workplane(offset=11).circle(53.5).loft())   # 입구 원뿔
neck = cq.Workplane('XZ', origin=(0, -1, 0)).circle(29.5).extrude(-15)
shaft = cq.Workplane('XZ', origin=(0, 13.5, 0)).circle(44.7).extrude(-86.5).intersect(cq.Workplane('YZ').polyline([(13.5, 37.3), (100, 37.3), (100, -29.9), (71.7, -29.9), (49.3, -34.3), (43.3, -34.3), (43.3, -29.9), (13.5, -29.9)]).close().extrude(50, both=True))
shaft = shaft.cut(cq.Workplane('XZ', origin=(0, 100, 0)).circle(24.5).extrude(4.5))
r = clip.union(neck).union(shaft).rotate((0, 0, 0), (0, 1, 0), -12.5)
