import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-76,2),(-13,-52)).segment((13,-52)).segment((76,2)).segment((63,28)).segment((0,-26)).segment((-63,28)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(5,200,6).translate((-15,0,7))).cut(cq.Workplane('XY').box(7,200,8).translate((11,0,7)))