import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-79,11),(-5,-38)).segment((5,-38)).segment((79,11)).segment((69,32)).segment((0,-17)).segment((-69,32)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(3)