# 등판: 바탕(통짜) ∩ U 껍질(두께 3) — 바깥 곡선은 단면에서 잰 7 점 스플라인
pts = [(0, 70.3), (5, 56.5), (10, 48.5), (20, 39), (30, 34), (40, 31.3), (50, 31), (60, 31.3), (70, 34), (80, 39), (90, 48.5), (95, 56.5), (100, 70.3)]
def D(): return cq.Workplane("XZ", origin=(0, 110, 0)).spline(pts).close()
outer = D().extrude(120)
inner = D().offset2D(-3).extrude(120)
껍질 = outer.cut(inner).cut(inner.translate((0, 0, 10)))
r = 바탕.intersect(껍질)
