import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-95,21),(-8,-71)).segment((8,-71)).segment((95,21)).segment((81,49)).segment((0,-43)).segment((-81,49)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(11,200,40).translate((-21,0,21))).cut(cq.Workplane('XY').box(8,200,12).translate((-5,0,21)))