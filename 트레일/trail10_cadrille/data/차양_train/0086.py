import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-75,-3),(-8,-43)).segment((8,-43)).segment((75,-3)).segment((65,18)).segment((0,-22)).segment((-65,18)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(7,200,6).translate((-28,0,13))).cut(cq.Workplane('XY').box(3,200,22).translate((-21,0,13)))