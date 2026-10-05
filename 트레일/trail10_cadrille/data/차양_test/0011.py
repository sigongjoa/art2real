import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-86,-5),(-10,-41)).segment((10,-41)).segment((86,-5)).segment((76,15)).segment((0,-21)).segment((-76,15)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(4,200,16).translate((35,0,12))).cut(cq.Workplane('XY').box(4,200,20).translate((-37,0,12)))