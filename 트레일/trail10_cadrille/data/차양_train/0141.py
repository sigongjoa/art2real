import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-90,17),(-10,-30)).segment((10,-30)).segment((90,17)).segment((80,37)).segment((0,-10)).segment((-80,37)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(7,200,10).translate((-12,0,8)))