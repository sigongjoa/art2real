import cadquery as cq
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
# 앞판: 정면 윤곽 ∩ 옆 윤곽(앞으로 숙인 위) ∩ 위에서 본 활 모양
fs = cq.Workplane('XZ').polyline([(-50, 90.6), (50, 90.6), (60, 50), (74.6, 30), (74.6, -60), (60, -72), (20, -80), (0, -90.6), (-20, -80), (-60, -72), (-74.6, -60), (-74.6, 30), (-60, 50)]).close().extrude(120, both=True)
fp = cq.Workplane('YZ').polyline([(-77, -91), (-62, -91), (-62, -60), (-52, -46), (-52, 1), (-55, 30), (-56, 50), (-40, 74), (-40, 90.6), (-60, 90.6), (-75, 80), (-100, 50), (-100, 10), (-77, -40)]).close().extrude(80, both=True)
ft = cq.Workplane('XY', origin=(0, 0, -100)).polyline([(-74.6, -62), (0, -100), (74.6, -62), (74.6, -40), (-74.6, -40)]).close().extrude(200)
front = fs.intersect(fp).intersect(ft)
# 앞면 V 홈(갈매기)
band = cq.Workplane('XZ').polyline([(-80, 16), (0, -40), (80, 16), (80, 6), (0, -50), (-80, 6)]).close().extrude(120, both=True)
front = front.cut(band.cut(front.translate((0, 8, 0))))
# 뒤판(아래 가운데 홈) + 뒤 혹
back = cq.Workplane('XY', origin=(0, 0, -73)).polyline([(-74.6, 14), (74.6, 14), (74.6, 39), (26, 51), (-26, 51), (-74.6, 39)]).close().extrude(103)
back = back.intersect(cq.Workplane('XZ').polyline([(-74.6, -73), (74.6, -73), (74.6, 30), (60, 55), (-60, 55), (-74.6, 30)]).close().extrude(100, both=True))
back = back.cut(cq.Workplane('XZ', origin=(0, 0, -80)).circle(44).extrude(-70)).cut(box(-12, 12, 0, 60, -33, -7))
hump = cq.Workplane('YZ').polyline([(14, -7), (46, 1), (61, 12), (73, 28), (82, 34), (100, 58), (93, 61), (67, 75), (43, 78), (17, 73), (15, 90.6), (2, 90.6), (2, 9), (14, 9)]).close().extrude(55, both=True)
hump = hump.intersect(cq.Workplane('XY', origin=(0, 0, -10)).polyline([(-60, 2), (60, 2), (60, 50), (25, 63), (17, 74), (8, 100), (-8, 100), (-17, 74), (-25, 63), (-60, 50)]).close().extrude(110))
# 위 틀
top = box(-53, 53, -45, 15, 74, 90.6).cut(box(-36, 36, -40, 2, 70, 95))
r = front.union(back).union(hump).union(top)
