import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-89,1),(-11,-69)).segment((11,-69)).segment((89,1)).segment((72,35)).segment((0,-35)).segment((-72,35)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(11,200,34).translate((-34,0,18))).cut(cq.Workplane('XY').box(12,200,34).translate((-14,0,18)))