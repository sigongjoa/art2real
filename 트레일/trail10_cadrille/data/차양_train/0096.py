import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-83,-1),(-6,-43)).segment((6,-43)).segment((83,-1)).segment((72,21)).segment((0,-21)).segment((-72,21)).close().assemble().finalize().extrude(18).cut(cq.Workplane('XY').box(3,200,10).translate((30,0,9))).cut(cq.Workplane('XY').box(6,200,10).translate((11,0,9)))