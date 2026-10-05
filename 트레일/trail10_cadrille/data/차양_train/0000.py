import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-63,20),(-5,-43)).segment((5,-43)).segment((63,20)).segment((50,46)).segment((0,-17)).segment((-50,46)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(4,200,6).translate((16,0,9))).cut(cq.Workplane('XY').box(3,200,18).translate((30,0,9)))