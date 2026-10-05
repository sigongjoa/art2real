import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-83,10),(-7,-55)).segment((7,-55)).segment((83,10)).segment((72,32)).segment((0,-33)).segment((-72,32)).close().assemble().finalize().extrude(21).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(3,200,18).translate((-5,0,11))).cut(cq.Workplane('XY').box(8,200,8).translate((29,0,11)))