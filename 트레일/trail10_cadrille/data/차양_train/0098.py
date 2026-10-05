import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-85,5),(-11,-49)).segment((11,-49)).segment((85,5)).segment((75,25)).segment((0,-29)).segment((-75,25)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(3,200,8).translate((-25,0,7))).cut(cq.Workplane('XY').box(5,200,8).translate((-10,0,7)))