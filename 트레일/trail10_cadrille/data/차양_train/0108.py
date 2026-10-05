import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-72,17),(-10,-33)).segment((10,-33)).segment((72,17)).segment((64,34)).segment((0,-16)).segment((-64,34)).close().assemble().finalize().extrude(14).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(8,200,14).translate((35,0,7))).cut(cq.Workplane('XY').box(7,200,14).translate((-29,0,7)))