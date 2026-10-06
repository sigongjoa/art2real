import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-94,2),(-14,-68)).segment((14,-68)).segment((94,2)).segment((76,38)).segment((0,-32)).segment((-76,38)).close().assemble().finalize().extrude(36).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(8,200,6).translate((-14,0,18)))