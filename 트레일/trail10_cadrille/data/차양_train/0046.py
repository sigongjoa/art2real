import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-58,16),(-14,-40)).segment((14,-40)).segment((58,16)).segment((48,36)).segment((0,-20)).segment((-48,36)).close().assemble().finalize().extrude(21).edges('>Z').chamfer(3)