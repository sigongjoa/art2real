import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-93,25),(-6,-51)).segment((6,-51)).segment((93,25)).segment((75,62)).segment((0,-14)).segment((-75,62)).close().assemble().finalize().extrude(31).edges('>Z').chamfer(7)