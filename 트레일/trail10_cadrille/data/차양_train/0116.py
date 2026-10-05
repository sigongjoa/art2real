import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-78,-3),(-10,-25)).segment((10,-25)).segment((78,-3)).segment((70,13)).segment((0,-9)).segment((-70,13)).close().assemble().finalize().extrude(21).cut(cq.Workplane('XY').box(5,200,14).translate((0,0,11)))