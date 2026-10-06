import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-91,5),(-10,-71)).segment((10,-71)).segment((91,5)).segment((77,34)).segment((0,-42)).segment((-77,34)).close().assemble().finalize().extrude(39).edges('>Z').chamfer(11)