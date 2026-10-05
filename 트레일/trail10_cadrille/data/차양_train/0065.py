import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-94,5),(-10,-37)).segment((10,-37)).segment((94,5)).segment((80,33)).segment((0,-9)).segment((-80,33)).close().assemble().finalize().extrude(17).cut(cq.Workplane('XY').box(8,200,8).translate((0,0,9)))