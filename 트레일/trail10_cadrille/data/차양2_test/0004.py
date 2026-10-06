import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-97,3),(-11,-73)).segment((11,-73)).segment((97,3)).segment((77,43)).segment((0,-33)).segment((-77,43)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(11,200,24).translate((-36,0,13))).cut(cq.Workplane('XY').box(7,200,12).translate((21,0,13)))