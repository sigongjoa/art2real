import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-92,15),(-15,-65)).segment((15,-65)).segment((92,15)).segment((77,45)).segment((0,-35)).segment((-77,45)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(12,200,22).translate((0,0,17)))