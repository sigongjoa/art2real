import cadquery as cq
def yz(P, x0, x1): return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline(P).close().extrude(x1 - x0)
slab = yz([(-11.1, 100), (-61.3, 92.3), (-64.7, 87.6), (-41.1, -66.5), (-36.3, -73), (19.1, -99.9)], -39.3, 39.3)
spur = yz([(4.7, -3.2), (36.4, 1.6), (54.2, 1.2), (64.7, -67.1), (43.4, -96.2), (19.1, -99.9), (0, -60)], -13.4, 13.4)
slab = slab.intersect(cq.Workplane("XZ").polyline([(-26.4, 101), (26.4, 101), (39.3, 88), (39.3, -60), (26.4, -95), (-26.4, -95), (-39.3, -60), (-39.3, 88)]).close().extrude(80, both=True))
b = slab.union(spur)
for s in (1, -1):
    b = b.cut(yz([(-70, 27.8), (-30.6, 32.6), (-21, -30.4), (-70, -37.8)], 7.9 if s > 0 else -23.6, 23.6 if s > 0 else -7.9))
r = b
