import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-91,-2),(-10,-40)).segment((10,-40)).segment((91,-2)).segment((79,22)).segment((0,-16)).segment((-79,22)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(4,200,20).translate((19,0,11)))