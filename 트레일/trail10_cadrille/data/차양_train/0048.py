import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-83,2),(-10,-52)).segment((10,-52)).segment((83,2)).segment((70,29)).segment((0,-25)).segment((-70,29)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(7,200,20).translate((-26,0,12))).cut(cq.Workplane('XY').box(3,200,18).translate((-15,0,12)))