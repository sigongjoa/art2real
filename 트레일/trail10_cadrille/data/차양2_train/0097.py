import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-95,-3),(-7,-65)).segment((7,-65)).segment((95,-3)).segment((77,33)).segment((0,-29)).segment((-77,33)).close().assemble().finalize().extrude(38).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(12,200,12).translate((-34,0,19))).cut(cq.Workplane('XY').box(11,200,18).translate((-29,0,19)))