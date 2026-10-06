import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-90,10),(-6,-60)).segment((6,-60)).segment((90,10)).segment((77,37)).segment((0,-33)).segment((-77,37)).close().assemble().finalize().extrude(33).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(9,200,28).translate((0,0,17)))