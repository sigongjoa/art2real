import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-90,17),(-15,-69)).segment((15,-69)).segment((90,17)).segment((77,44)).segment((0,-42)).segment((-77,44)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(7,200,18).translate((35,0,12))).cut(cq.Workplane('XY').box(6,200,12).translate((-16,0,12)))