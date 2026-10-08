import cadquery as cq
S = [(-100, -14.1), (-25, -89.1), (42.4, -89.1), (99, -31.6), (99.4, 22.5), (97.5, 28.6), (37.4, 88), (32.1, 89.1), (-19.5, 86.1), (-42, 64.9), (-27.3, 35.3), (-34.8, 27.7), (-55.8, 27.4), (-59.6, 26.1)]
core = cq.Workplane('YZ').polyline(S).close().extrude(72.1, both=True)
inner = cq.Workplane('YZ').polyline(S).close().offset2D(-6, 'intersection').extrude(30, both=True)
band = cq.Workplane('XY').box(52.4, 300, 200).translate((0, 0, 120)).union(cq.Workplane('XY').box(52.4, 200, 300).translate((0, 140, 0)))
core = core.cut(band.cut(inner))
F = [(-37.9, 61.2), (-2.1, 24), (-21.7, 4.4), (-15.1, -2.2), (-37.6, -24.7), (-59.2, -16.6), (-69.5, -27), (-68.4, -30.1), (-46.9, -32.4), (-24.7, -53.8), (-12.8, -65.3), (11.7, -89.1), (11.7, -100), (-120, -100), (-120, 70), (-45, 70)]
core = core.cut(cq.Workplane('YZ').polyline(F).close().extrude(50.8, both=True))
sock = cq.Workplane('XZ').polyline([(0, -95), (21.5, -95), (21.5, -62), (25.9, -47), (25, -38), (18.4, -26.3), (5.9, -19.4), (0, -19.4)]).close().revolve(360, (0, 0, 0), (0, 1, 0)).translate((0, -2, 0))
core = core.cut(sock)
D = [(34.7, -16.7), (-6.4, 25.4), (-47, -14.3), (-5.5, -56.5)]
for s in (1, -1):
    pod = cq.Workplane('YZ', origin=(72.1 if s > 0 else -83, 0, 0)).polyline(D).close().extrude(10.9)
    core = core.union(pod.faces('>X' if s > 0 else '<X').chamfer(3))
r = core
