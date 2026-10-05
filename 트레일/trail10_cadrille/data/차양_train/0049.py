import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-93,8),(-5,-42)).segment((5,-42)).segment((93,8)).segment((79,36)).segment((0,-14)).segment((-79,36)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(5)