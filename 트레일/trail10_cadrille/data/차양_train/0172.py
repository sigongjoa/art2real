import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-95,16),(-10,-43)).segment((10,-43)).segment((95,16)).segment((84,39)).segment((0,-20)).segment((-84,39)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(8,200,22).translate((-24,0,14))).cut(cq.Workplane('XY').box(7,200,24).translate((15,0,14)))