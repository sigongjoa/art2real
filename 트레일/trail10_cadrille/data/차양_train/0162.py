import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-95,20),(-10,-32)).segment((10,-32)).segment((95,20)).segment((86,38)).segment((0,-14)).segment((-86,38)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(6)