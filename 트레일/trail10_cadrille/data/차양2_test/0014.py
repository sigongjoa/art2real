import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-97,-2),(-8,-64)).segment((8,-64)).segment((97,-2)).segment((81,30)).segment((0,-32)).segment((-81,30)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,10).translate((30,0,17))).cut(cq.Workplane('XY').box(12,200,24).translate((-14,0,17)))