import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-94,12),(-7,-31)).segment((7,-31)).segment((94,12)).segment((84,32)).segment((0,-11)).segment((-84,32)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(4,200,8).translate((44,0,14))).cut(cq.Workplane('XY').box(3,200,10).translate((33,0,14)))