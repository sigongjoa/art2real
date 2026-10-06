import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-97,0),(-18,-64)).segment((18,-64)).segment((97,0)).segment((80,34)).segment((0,-30)).segment((-80,34)).close().assemble().finalize().extrude(32).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(11,200,26).translate((0,0,16)))