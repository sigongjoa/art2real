import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-78,15),(-6,-35)).segment((6,-35)).segment((78,15)).segment((71,30)).segment((0,-20)).segment((-71,30)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(5,200,16).translate((0,0,11)))