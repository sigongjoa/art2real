import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-86,4),(-12,-42)).segment((12,-42)).segment((86,4)).segment((79,19)).segment((0,-27)).segment((-79,19)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(5)