import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-92,4),(-12,-45)).segment((12,-45)).segment((92,4)).segment((79,30)).segment((0,-19)).segment((-79,30)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(4)