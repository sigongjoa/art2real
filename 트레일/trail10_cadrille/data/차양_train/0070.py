import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-94,0),(-7,-47)).segment((7,-47)).segment((94,0)).segment((87,15)).segment((0,-32)).segment((-87,15)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(4,200,12).translate((-26,0,11))).cut(cq.Workplane('XY').box(6,200,22).translate((-11,0,11)))