import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-87,-3),(-15,-52)).segment((15,-52)).segment((87,-3)).segment((71,30)).segment((0,-19)).segment((-71,30)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(12,200,16).translate((30,0,20))).cut(cq.Workplane('XY').box(10,200,18).translate((21,0,20)))