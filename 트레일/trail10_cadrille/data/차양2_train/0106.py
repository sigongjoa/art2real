import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-89,19),(-16,-73)).segment((16,-73)).segment((89,19)).segment((75,47)).segment((0,-45)).segment((-75,47)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(6)