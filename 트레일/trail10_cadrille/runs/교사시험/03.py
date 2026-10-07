import cadquery as cq
z0 = -55.5
A = [(-39.6, -100), (39.6, -100), (48.7, -92.6), (60.3, -35), (52.4, -4.4), (-52.4, -4.4), (-60.3, -35), (-48.7, -92.6)]   # 앞 · 볼록
B = [(-52.4, -20), (52.4, -20), (52.4, 81.1), (33.6, 99.9), (-33.6, 99.9), (-52.4, 81.1)]   # 뒤 · 볼록 · 앞과 겹침
body = None
for Q in (A, B):   # 위: 10° 기울기 · 아래 4.6: 안으로 깎인 밑단
    for h, t in ((60, 10), (-4.6, 40)):
        p = cq.Workplane('XY', origin=(0, 0, -50.9)).polyline(Q).close().extrude(h, taper=t)
        body = p if body is None else body.union(p)
side = cq.Workplane('YZ').polyline([(-95.3, -55.5), (95.9, -55.5), (100, -50.9), (93.9, -5), (85.4, 2.3), (-4.7, 2.3), (-32.2, 30.2), (-39.1, 30.2), (-100, -19.1), (-100, -50.9)]).close().extrude(70, both=True)
r = body.intersect(side)
r = r.union(cq.Workplane('XY', origin=(0, 22.5, 0)).circle(21.2).extrude(10))
ball = cq.Workplane('XY').sphere(29).translate((0, 22.5, 25))
ball = ball.cut(cq.Workplane('XY').box(15.6, 80, 60).translate((0, 22.5, 43.6))).cut(cq.Workplane('XZ', origin=(0, 60, 13.6)).circle(7.8).extrude(80))
ball = ball.cut(cq.Workplane('YZ').center(22.5, 32).slot2D(30, 18, 90).extrude(50, both=True))
r = r.union(ball)
