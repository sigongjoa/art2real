import cadquery as cq
B = lambda sx, sy, sz, x, y, z: cq.Workplane('XY').box(sx, sy, sz).translate((x, y, z))
palm = B(106, 109, 50, 2, 4.5, -20).edges('|Z').fillet(8)
ball = cq.Workplane().sphere(47).translate((2, 7, -58)).intersect(B(200, 200, 100, 0, 0, -50))
ball = ball.cut(B(120, 40, 26, 2, 7, -88)).cut(B(59, 40, 20, 2.5, 7, -45))
r = palm.union(ball)
r = r.union(B(33, 107, 53, -37.5, 7.5, 21.5).edges('|Z').fillet(6))     # 손가락 뿌리
r = r.union(B(30, 64, 53, 33, -28, 21.5).edges('|Z').fillet(6))       # 엄지
def rod(a, b, rad):   # 팔각 막대 a→b (양끝 조금 늘림)
    a, b = cq.Vector(*a), cq.Vector(*b); d = (b - a).normalized(); a = a - d * rad * 0.4; L = (b - a).Length + rad * 0.4
    return cq.Workplane(cq.Plane(origin=a, xDir=cq.Vector(0, 1, 0).cross(d) if abs(d.y) < 0.9 else cq.Vector(1, 0, 0), normal=d)).polygon(8, 2 * rad).extrude(L)
P = [(-38, 40), (-38, 62), (-27, 86), (-8, 88), (15, 88), (28, 78), (28, 48)]
for y in (-28, -4.5, 19, 43):                                          # 손가락 = 팔각 막대 꺾은선
    for (x0, z0), (x1, z1) in zip(P, P[1:]):
        r = r.union(rod((x0, y, z0), (x1, y, z1), 11.5))
r = r.union(rod((32, -45, 28), (32, -45, 84), 9))                       # 엄지 끝
r = r.intersect(B(200, 200, 199.6, 0, 0, 0))
