import cadquery as cq
z0 = -28.8
side = [(-97, 12), (-80, -12), (-50, -40), (-25, -58), (0, -66.1), (25, -58), (50, -40), (80, -12), (97, 12)]
plan = cq.Workplane('XY', origin=(0, 0, z0)).moveTo(-97, 40).spline(side, includeCurrent=False).lineTo(97, 40).close().extrude(60, taper=5)
plan = cq.Workplane('XY', origin=(0, 0, z0)).moveTo(-97, 40).lineTo(*side[0]).spline(side, includeCurrent=False).lineTo(97, 40).close().extrude(60, taper=5)
prof = cq.Workplane('YZ').polyline([(16, z0), (16, -0.4), (-57, 28.8), (-70, 28.8), (-70, z0)]).close().extrude(110, both=True)
body = plan.intersect(prof)
stem = cq.Workplane('XZ', origin=(0, 10, 0)).center(0, (z0 - 2) / 2).rect(46, -2 - z0).extrude(-56.1).edges('|Y and >Z').fillet(8)
r = body.union(stem)
