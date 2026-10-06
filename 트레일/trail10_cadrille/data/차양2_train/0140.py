import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-93,22),(-10,-52)).segment((10,-52)).segment((93,22)).segment((75,59)).segment((0,-15)).segment((-75,59)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(12)