import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-75,-5),(-14,-25)).segment((14,-25)).segment((75,-5)).segment((68,9)).segment((0,-11)).segment((-68,9)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,12).translate((-35,0,14)))