import cadquery as cq
B = lambda sx, sy, sz, x, y, z: cq.Workplane('XY').box(sx, sy, sz).translate((x, y, z))
import math
def el(y, f): return cq.Wire.makeEllipse(99 * f, 76 * f, cq.Vector(0, y, -1), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1))
dome = cq.Solid.makeLoft([el(y, math.sqrt(1 - (y / 60) ** 2)) for y in (0, 15, 30, 40, 48, 54, 58)])
r = cq.Workplane().add(dome).union(cq.Workplane('XZ', origin=(0, 0, 0)).center(0, -1).ellipse(76, 99).extrude(80))
r = r.cut(B(300, 300, 300, 0, -150 - 10, 150 + 22))           # 얼굴 쪽(y<-10, z>22)은 가면으로
r = r.cut(B(300, 100, 300, 0, -125, 0))                        # 목 평면 y=-75
mask = cq.Workplane('XZ', origin=(0, -10, 0)).polyline([(-72, 0), (-72, 20), (-60, 44), (-40, 51), (-20, 68), (0, 81), (20, 68), (40, 51), (60, 44), (72, 20), (72, 0)]).close().extrude(68)
r = r.union(mask)
r = r.cut(cq.Workplane('XZ', origin=(0, -17, 0)).center(0, -25.5).ellipse(63, 54.5).extrude(80))   # 목 구멍
r = r.cut(B(140, 8, 100, 0, -6, 72)).cut(B(62, 9, 100, 0, -5.5, 17))                              # 이마-가면 틈
r = r.union(B(40, 13, 40, 0, -23.5, -20))
for sx in (-1, 1):
    r = r.union(B(16, 58, 44, sx * 36, -46, -20))                                 # 목 안 세로 막대
    r = r.union(B(21, 65, 57, sx * 81, -43, -27).edges('|Z').chamfer(8))           # 볼판
    fin = B(85, 12, 7, 42.5, 0, 0).rotate((0, 0, 0), (0, 1, 0), 13).rotate((0, 0, 0), (0, 0, 1), 35).translate((12, 22, 90))
    r = r.union(fin.mirror('YZ') if sx < 0 else fin)
r = r.union(B(38, 45, 120, 0, 61, 2))                                              # 등줄기
r = r.union(B(24, 26, 38, 0, -71, 59))                                             # 턱 돌기
r = r.intersect(B(200, 200, 200, 0, 0, 0))
