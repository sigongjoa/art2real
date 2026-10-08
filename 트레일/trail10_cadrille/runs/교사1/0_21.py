import cadquery as cq
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def both(b):
    return b.union(b.mirror('YZ'))
h = [(33.6, -14.7), (85.3, -9.1), (93.1, -8.4), (101, -4.2), (101, 9.4), (90.7, 9.4), (91, 3.8), (87, 0)]
plan = h + [(-x, y) for x, y in h[::-1]]
front = [(-25.5, -40.8), (25.5, -40.8), (89.6, -25), (100.2, -23.7), (91.1, 40.8), (-91.1, 40.8), (-100.2, -23.7), (-89.6, -25)]
r = cq.Workplane('XY', origin=(0, 0, -41)).polyline(plan).close().extrude(82)
r = r.intersect(cq.Workplane('XZ').polyline(front).close().extrude(30, both=True))
r = r.union(both(box(45, 67.9, -1, 14.7, 8.1, 40.8)))                     # 뒤 탭
r = r.cut(box(-42.5, 42.5, -6, 1, 7.3, 42)).cut(box(-42.5, 42.5, -9.9, 1, 26, 42))   # 뒤 오목
r = r.cut(box(-31.2, 31.2, -20, -10.9, -11.6, 22.1))                      # 앞 가운데 판
r = r.cut(both(box(44.8, 59.9, -20, -9, -10, 22))).cut(both(box(67, 83, -20, -6.5, -8, 22)))   # 앞 옆 판
r = r.cut(both(box(58.5, 65.6, -20, 3.6, 13, 24)))                       # 작은 홈
r = r.cut(both(box(14.2, 21.8, -30, 30, -10, 10))).cut(both(box(48.5, 55.4, -30, 30, -8.3, 5.9)))   # 관통 슬롯
