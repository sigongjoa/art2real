import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-83,-1),(-10,-46)).segment((10,-46)).segment((83,-1)).segment((69,27)).segment((0,-18)).segment((-69,27)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(5,200,8).translate((0,0,12)))