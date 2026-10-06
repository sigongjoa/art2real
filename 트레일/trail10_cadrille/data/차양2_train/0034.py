import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-86,11),(-8,-67)).segment((8,-67)).segment((86,11)).segment((70,44)).segment((0,-34)).segment((-70,44)).close().assemble().finalize().extrude(30).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,10).translate((36,0,15)))