import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-79,4),(-14,-29)).segment((14,-29)).segment((79,4)).segment((71,21)).segment((0,-12)).segment((-71,21)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(4,200,16).translate((0,0,11)))