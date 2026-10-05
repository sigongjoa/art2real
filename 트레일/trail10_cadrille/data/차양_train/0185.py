import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-68,16),(-10,-25)).segment((10,-25)).segment((68,16)).segment((61,30)).segment((0,-11)).segment((-61,30)).close().assemble().finalize().extrude(10).edges('>Z').chamfer(2)