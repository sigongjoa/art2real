import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-88,21),(-13,-52)).segment((13,-52)).segment((88,21)).segment((72,54)).segment((0,-19)).segment((-72,54)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(10,200,36).translate((-11,0,21))).cut(cq.Workplane('XY').box(6,200,18).translate((31,0,21)))