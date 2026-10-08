import cadquery as cq
def pyr(base, apex):
    V = [cq.Vector(*p) for p in base]; A = cq.Vector(*apex)
    F = [cq.Face.makeFromWires(cq.Wire.makePolygon(V, close=True))]
    F += [cq.Face.makeFromWires(cq.Wire.makePolygon([V[i], V[(i + 1) % len(V)], A], close=True)) for i in range(len(V))]
    return cq.Workplane('XY').add(cq.Solid.makeSolid(cq.Shell.makeShell(F)).fix())
z0 = -23.4
prof = [(0, z0), (92, z0), (92, -11), (84, 10), (82, 16), (74, 16), (73, 6), (58, 6), (57, 4), (20, 4), (18, 15), (14, 15), (12, 11), (0, 11)]
hub = cq.Workplane('XZ').polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((100, -100, 0))
r = hub
r = r.union(pyr([(-36, 36, z0), (13, -46, z0), (50.5, -50.5, z0), (46, -13, z0)], (47.5, -47.5, 21.5)))
r = r.union(pyr([(-100, -100, z0), (30, -100, z0), (-2, -78, z0)], (23.2, -100, 23.3)))
r = r.union(pyr([(100, 100, z0), (78, 2, z0), (100, -30, z0)], (100, -23.2, 23.3)))
r = r.intersect(cq.Workplane('XY').box(200, 200, 60))
