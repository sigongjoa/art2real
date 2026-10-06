import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-93,9),(-12,-46)).segment((12,-46)).segment((93,9)).segment((79,37)).segment((0,-18)).segment((-79,37)).close().assemble().finalize().extrude(38).edges('>Z').chamfer(9)