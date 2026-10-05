import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-65,17),(-14,-39)).segment((14,-39)).segment((65,17)).segment((54,39)).segment((0,-17)).segment((-54,39)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(7,200,6).translate((-5,0,12))).cut(cq.Workplane('XY').box(8,200,16).translate((17,0,12)))