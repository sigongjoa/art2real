import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-58,18),(-10,-25)).segment((10,-25)).segment((58,18)).segment((48,38)).segment((0,-5)).segment((-48,38)).close().assemble().finalize().extrude(23).cut(cq.Workplane('XY').box(3,200,12).translate((5,0,12)))