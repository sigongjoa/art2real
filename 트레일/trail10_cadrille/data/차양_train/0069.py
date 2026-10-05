import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-68,-4),(-12,-46)).segment((12,-46)).segment((68,-4)).segment((58,17)).segment((0,-25)).segment((-58,17)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(4)