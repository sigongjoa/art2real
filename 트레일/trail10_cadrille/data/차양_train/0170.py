import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-88,1),(-8,-31)).segment((8,-31)).segment((88,1)).segment((78,22)).segment((0,-10)).segment((-78,22)).close().assemble().finalize().extrude(17).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(8,200,6).translate((0,0,9)))