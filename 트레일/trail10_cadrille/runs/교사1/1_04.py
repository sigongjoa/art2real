import cadquery as cq
H = [(44, -100), (86, -37), (95, -20), (98, 0), (98, 100), (78, 100), (49, 72), (17.5, 100)]
O = H + [(-x, z) for x, z in reversed(H)]
out = cq.Workplane('XZ').polyline(O).close().extrude(-200, both=True)   # (x,z) 윤곽 · y 전체
low = cq.Workplane('XY').box(200, 52, 138.4).translate((0, 2, -100 + 69.2))
up = cq.Workplane('XY', origin=(0, 0, 38.4)).polyline([(-100, -24), (100, -24), (100, 28), (82, 28), (61, 0), (-61, 0), (-82, 28), (-100, 28)]).close().extrude(62)
r = low.union(up).intersect(out)
for sx in (-1, 1):   # 볼 비탈
    c = cq.Workplane('XY').box(100, 100, 300).translate((50, -50, 0)).rotate((0, 0, 0), (0, 0, 1), 37.6).translate((55, -20, 0))
    r = r.cut(c.mirror('YZ') if sx < 0 else c)
    r = r.union(cq.Workplane('YZ', origin=(sx * 55 - 15, 0, 0)).polyline([(28, -37), (72.3, 2.4), (72.3, 38.4), (28, 38.4)]).close().extrude(30))
crest = cq.Workplane('YZ', origin=(-17.5, 0, 0)).polyline([(0, 100), (-50, 100), (-72, 41), (-42, 28), (-42, 0), (0, 0)]).close().extrude(35)
crest = crest.edges('|Z or |Y').chamfer(6) if False else crest
lip = cq.Workplane('XY').box(62, 30, 19).edges('|Y').chamfer(5).translate((0, -20, -23.5))
r = r.union(crest).union(lip)
