import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-79,14),(-4,-38)).segment((4,-38)).segment((79,14)).segment((66,40)).segment((0,-12)).segment((-66,40)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(3)