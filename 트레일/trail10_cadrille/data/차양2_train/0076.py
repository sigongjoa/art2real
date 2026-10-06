import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-96,5),(-10,-53)).segment((10,-53)).segment((96,5)).segment((82,33)).segment((0,-25)).segment((-82,33)).close().assemble().finalize().extrude(36).cut(cq.Workplane('XY').box(8,200,18).translate((0,0,18)))