import cadquery as cq
c1, c2 = (-35.2, -33.6), (51.1, 49.6)
sk = cq.Sketch().push([c1]).circle(64.9).push([c2]).circle(32).reset().edges().hull().reset().push([c1]).circle(30.5, mode='s')
plate = cq.Workplane('XZ').placeSketch(sk).extrude(30.6, both=True)
ball = cq.Workplane('XY').sphere(48.9).translate((c2[0], 0, c2[1])).intersect(cq.Workplane('XY').box(200, 200, 97.6).translate((c2[0], 0, c2[1])))   # 극점 잘라 STL 닫기
r = plate.union(ball)
