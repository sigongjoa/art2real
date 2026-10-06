import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-88,20),(-8,-52)).segment((8,-52)).segment((88,20)).segment((70,57)).segment((0,-15)).segment((-70,57)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(11,200,18).translate((-31,0,14)))