import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-92,4),(-11,-56)).segment((11,-56)).segment((92,4)).segment((74,40)).segment((0,-20)).segment((-74,40)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(5,200,22).translate((-20,0,21))).cut(cq.Workplane('XY').box(8,200,34).translate((35,0,21)))