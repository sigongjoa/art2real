import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-97,6),(-10,-65)).segment((10,-65)).segment((97,6)).segment((79,42)).segment((0,-29)).segment((-79,42)).close().assemble().finalize().extrude(38).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(9,200,20).translate((0,0,19)))