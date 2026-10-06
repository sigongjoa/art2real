import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-97,9),(-11,-51)).segment((11,-51)).segment((97,9)).segment((81,42)).segment((0,-18)).segment((-81,42)).close().assemble().finalize().extrude(31).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(12,200,6).translate((46,0,16))).cut(cq.Workplane('XY').box(10,200,14).translate((45,0,16)))