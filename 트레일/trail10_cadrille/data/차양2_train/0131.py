import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-97,14),(-17,-68)).segment((17,-68)).segment((97,14)).segment((84,40)).segment((0,-42)).segment((-84,40)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(10,200,18).translate((0,0,18)))