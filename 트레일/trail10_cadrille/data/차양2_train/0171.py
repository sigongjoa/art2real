import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-88,16),(-12,-45)).segment((12,-45)).segment((88,16)).segment((76,41)).segment((0,-20)).segment((-76,41)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(5)