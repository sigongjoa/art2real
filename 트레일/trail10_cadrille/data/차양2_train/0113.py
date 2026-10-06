import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-92,20),(-11,-71)).segment((11,-71)).segment((92,20)).segment((75,54)).segment((0,-37)).segment((-75,54)).close().assemble().finalize().extrude(33).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(6,200,24).translate((5,0,17))).cut(cq.Workplane('XY').box(9,200,14).translate((-28,0,17)))