import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-88,3),(-10,-55)).segment((10,-55)).segment((88,3)).segment((72,35)).segment((0,-23)).segment((-72,35)).close().assemble().finalize().extrude(39).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(9,200,8).translate((0,0,20)))