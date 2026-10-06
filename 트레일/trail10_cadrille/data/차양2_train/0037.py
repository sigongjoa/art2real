import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-85,6),(-15,-67)).segment((15,-67)).segment((85,6)).segment((71,34)).segment((0,-39)).segment((-71,34)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(11,200,10).translate((29,0,14))).cut(cq.Workplane('XY').box(6,200,12).translate((35,0,14)))