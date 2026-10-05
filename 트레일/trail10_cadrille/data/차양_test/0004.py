import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-80,3),(-12,-50)).segment((12,-50)).segment((80,3)).segment((67,30)).segment((0,-23)).segment((-67,30)).close().assemble().finalize().extrude(21).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(3,200,18).translate((0,0,11)))