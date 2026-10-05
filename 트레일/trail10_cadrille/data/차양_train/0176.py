import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-76,15),(-10,-47)).segment((10,-47)).segment((76,15)).segment((68,31)).segment((0,-31)).segment((-68,31)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(5,200,22).translate((-37,0,12)))