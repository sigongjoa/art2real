import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-66,18),(-5,-49)).segment((5,-49)).segment((66,18)).segment((55,41)).segment((0,-26)).segment((-55,41)).close().assemble().finalize().extrude(21).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(5,200,18).translate((0,0,11)))