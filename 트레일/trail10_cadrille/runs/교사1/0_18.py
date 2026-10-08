import cadquery as cq
# 바깥: z 높이마다 타원(x 반폭 · y 앞뒤) 로프트 — 단면 꼭짓점에서 읽음
S = [(-85.8, 100, -23, 47), (-60, 98, -52, 70), (-30, 91, -87, 92), (-15, 85, -93, 92), (0, 80, -75, 95), (15, 73, -57, 93), (30, 64, -39, 94), (45, 54, -27, 86), (60, 41, -22, 72), (72, 26, -8, 55), (80, 10, 5, 32)]
sk = [cq.Wire.makeEllipse(a, (y1 - y0) / 2, cq.Vector(0, (y0 + y1) / 2, z), cq.Vector(0, 0, 1), cq.Vector(1, 0, 0)) for z, a, y0, y1 in S]
outer = cq.Workplane('XY').add(cq.Solid.makeLoft(sk, True))
crest = outer.translate((0, 0, 9)).intersect(cq.Workplane('XY').box(26, 140, 100).translate((0, 25, 45)))   # 볏
r = outer.union(crest).intersect(cq.Workplane('XY').box(220, 220, 171.6))
# 속: 구(극점은 z=70 에서 잘라 냄) + 아래로 원기둥
cav = cq.Workplane('XY').sphere(46).translate((0, 15, 27)).intersect(cq.Workplane('XY').box(100, 100, 100).translate((0, 15, 20))).union(cq.Workplane('XY', origin=(0, 15, -100)).circle(44).extrude(127))
r = r.cut(cav)
face = cq.Workplane('XZ', origin=(0, 15, 0)).polyline([(-42, -90), (42, -90), (42, 15), (34, 20), (34, 42), (14, 52), (-14, 52), (-34, 42), (-34, 20), (-42, 15)]).close().extrude(130)
r = r.cut(face).cut(cq.Workplane('XY').box(40, 240, 30).translate((0, 0, -80)))   # 얼굴 · 목 홈
