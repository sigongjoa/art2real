import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-92,0),(-6,-60)).segment((6,-60)).segment((92,0)).segment((78,28)).segment((0,-32)).segment((-78,28)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(6,200,24).translate((-6,0,18))).cut(cq.Workplane('XY').box(9,200,30).translate((36,0,18)))