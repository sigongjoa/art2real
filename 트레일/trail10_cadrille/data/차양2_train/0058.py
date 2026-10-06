import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-88,23),(-10,-52)).segment((10,-52)).segment((88,23)).segment((71,57)).segment((0,-18)).segment((-71,57)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(5,200,10).translate((21,0,13))).cut(cq.Workplane('XY').box(9,200,16).translate((-6,0,13)))