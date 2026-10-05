import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-61,4),(-4,-49)).segment((4,-49)).segment((61,4)).segment((51,25)).segment((0,-28)).segment((-51,25)).close().assemble().finalize().extrude(14).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,8).translate((30,0,7))).cut(cq.Workplane('XY').box(3,200,14).translate((-9,0,7)))