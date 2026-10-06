import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-98,2),(-18,-74)).segment((18,-74)).segment((98,2)).segment((80,38)).segment((0,-38)).segment((-80,38)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(12,200,18).translate((-33,0,19))).cut(cq.Workplane('XY').box(11,200,32).translate((-34,0,19)))