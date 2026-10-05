import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-94,15),(-7,-32)).segment((7,-32)).segment((94,15)).segment((86,32)).segment((0,-15)).segment((-86,32)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(8,200,16).translate((-9,0,11)))