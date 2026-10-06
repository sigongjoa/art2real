import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-88,23),(-14,-69)).segment((14,-69)).segment((88,23)).segment((75,49)).segment((0,-43)).segment((-75,49)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(8,200,20).translate((0,0,15)))