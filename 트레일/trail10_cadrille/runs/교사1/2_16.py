import cadquery as cq
V = cq.Vector
def pl(p, u):
    u = V(*u).normalized(); return cq.Plane(origin=p, xDir=u.cross(V(0, 1, 0)).normalized(), normal=u)
def cyl(p0, p1, R): return cq.Workplane(pl(p0, V(*p1) - V(*p0))).circle(R).extrude((V(*p1) - V(*p0)).Length)
def ball(p, R, u): return cq.Workplane(pl(p, u)).sphere(R)   # 극점은 u 방향 — 이웃 원통 안에 묻힌다
P = [(-16, 0, -66), (-24, 0, -25), (-17, 0, 0), (22, 0, 70)]
d = lambda a, b: V(*P[b]) - V(*P[a])
r = ball(P[0], 39, d(0, 1)).intersect(cq.Workplane('XY').box(200, 200, 100).translate((0, 0, -50)))
r = r.union(cyl(P[0], P[1], 31)).union(ball(P[1], 32, d(1, 2))).union(cyl(P[1], P[2], 33)).union(ball(P[2], 33, d(2, 3))).union(cyl(P[2], P[3], 34)).union(ball(P[3], 34, d(2, 3)))
r = r.intersect(cq.Workplane('XY').box(200, 200, 200))
slot = cq.Workplane('XZ').center(24, 100).rect(32, 60).extrude(60, both=True).union(cq.Workplane('XZ').center(24, 70).circle(16).extrude(60, both=True))
r = r.cut(slot).cut(cq.Workplane('XY').box(54, 28, 46).translate((-6, 0, -77.4)))
