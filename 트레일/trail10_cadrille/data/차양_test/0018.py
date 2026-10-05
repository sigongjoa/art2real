import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-69,7),(-8,-33)).segment((8,-33)).segment((69,7)).segment((58,29)).segment((0,-11)).segment((-58,29)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(3,200,8).translate((-14,0,12)))