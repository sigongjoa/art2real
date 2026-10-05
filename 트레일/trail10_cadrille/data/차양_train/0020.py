import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-82,1),(-5,-43)).segment((5,-43)).segment((82,1)).segment((72,22)).segment((0,-22)).segment((-72,22)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(5)