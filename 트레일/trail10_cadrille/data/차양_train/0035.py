import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-59,15),(-8,-25)).segment((8,-25)).segment((59,15)).segment((52,29)).segment((0,-11)).segment((-52,29)).close().assemble().finalize().extrude(21).edges('>Z').chamfer(3)