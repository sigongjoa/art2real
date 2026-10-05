import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-78,16),(-11,-29)).segment((11,-29)).segment((78,16)).segment((66,40)).segment((0,-5)).segment((-66,40)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(3,200,12).translate((0,0,12)))