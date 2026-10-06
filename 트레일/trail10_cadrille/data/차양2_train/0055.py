import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-90,3),(-16,-74)).segment((16,-74)).segment((90,3)).segment((72,40)).segment((0,-37)).segment((-72,40)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(12,200,38).translate((0,0,21)))