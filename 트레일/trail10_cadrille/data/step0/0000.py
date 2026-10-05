import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
r=w0.sketch().segment((-90,10),(-10,-40)).segment((10,-40)).segment((90,10)).segment((70,30)).segment((0,-10)).segment((-70,30)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(8,200,10).translate((0,0,24)))