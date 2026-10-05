import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-87,14),(-4,-31)).segment((4,-31)).segment((87,14)).segment((77,34)).segment((0,-11)).segment((-77,34)).close().assemble().finalize().extrude(17).edges('>Z').chamfer(3)