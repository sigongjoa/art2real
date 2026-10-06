import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-97,25),(-10,-54)).segment((10,-54)).segment((97,25)).segment((79,62)).segment((0,-17)).segment((-79,62)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(12,200,18).translate((0,0,20)))