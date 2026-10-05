import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-59,0),(-8,-47)).segment((8,-47)).segment((59,0)).segment((45,28)).segment((0,-19)).segment((-45,28)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(3,200,14).translate((0,0,12)))