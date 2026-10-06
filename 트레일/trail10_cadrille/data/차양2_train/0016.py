import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-86,-3),(-10,-72)).segment((10,-72)).segment((86,-3)).segment((70,30)).segment((0,-39)).segment((-70,30)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(5,200,24).translate((0,0,15)))