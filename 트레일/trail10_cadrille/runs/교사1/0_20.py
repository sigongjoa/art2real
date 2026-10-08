import cadquery as cq
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def ell(c, a, b, h):   # 타원체(극점은 z 로 · 위아래 살짝 잘라 극점 없앰)
    s = cq.Workplane('XY').sphere(1).intersect(box(-1, 1, -1, 1, -0.97, 0.97)).val().scale(1)
    import OCP
    from cadquery import Matrix
    m = Matrix([[a, 0, 0, c[0]], [0, b, 0, c[1]], [0, 0, h, c[2]]])
    return cq.Workplane('XY').add(s.transformGeometry(m))
# 바닥 판: 둥근 평면 · 윗면은 앞쪽(-y)으로 내려감
slab = cq.Workplane('XY', origin=(0, 0, -69.5)).center(0, -13).rect(190, 126).extrude(70).edges('|Z').fillet(40)
slab = slab.cut(cq.Workplane('YZ').polyline([(-120, -34 - 14), (-60, -34), (0, -11), (60, 10), (60, 60), (-120, 60)]).close().extrude(120, both=True))
lobes = ell((55, 28, 0), 37, 22, 62).union(ell((-55, 28, 0), 37, 22, 62)).intersect(box(-100, 100, -100, 100, -69.5, 70))
r = slab.union(lobes)
r = r.union(box(-20, 20, -93, -56, -30, 64).edges('|Y').fillet(8))      # 앞 기둥
r = r.union(cq.Workplane('XY').sphere(24).intersect(box(-30, 30, -30, 30, -23, 23)).translate((0, -35, 27)))   # 위 공(극점 잘림)
r = r.union(box(-8, 8, -45, -25, -30, 10))                                # 공 목
r = r.union(cq.Workplane('XY').sphere(22).intersect(box(-30, 30, -30, 30, -21, 21)).translate((0, 74, -47)))   # 뒤 아래 공
r = r.union(box(-10, 10, 40, 60, -57, -37))
cav = cq.Workplane('XY', origin=(0, -20, -70)).ellipse(45, 40).workplane(offset=50).ellipse(10, 10).loft()
r = r.cut(cav)
