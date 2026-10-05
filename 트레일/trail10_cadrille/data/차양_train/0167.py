import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-92,-2),(-8,-41)).segment((8,-41)).segment((92,-2)).segment((80,23)).segment((0,-16)).segment((-80,23)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(7,200,16).translate((-4,0,12)))