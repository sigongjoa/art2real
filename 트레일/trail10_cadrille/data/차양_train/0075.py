import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-72,-2),(-5,-49)).segment((5,-49)).segment((72,-2)).segment((62,18)).segment((0,-29)).segment((-62,18)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(8,200,12).translate((-12,0,8)))