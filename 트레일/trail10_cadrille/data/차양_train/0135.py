import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-71,9),(-14,-25)).segment((14,-25)).segment((71,9)).segment((61,29)).segment((0,-5)).segment((-61,29)).close().assemble().finalize().extrude(17).edges('>Z').chamfer(5)