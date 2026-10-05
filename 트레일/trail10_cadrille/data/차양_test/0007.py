import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-79,-2),(-4,-43)).segment((4,-43)).segment((79,-2)).segment((66,25)).segment((0,-16)).segment((-66,25)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(3,200,14).translate((23,0,9))).cut(cq.Workplane('XY').box(3,200,6).translate((19,0,9)))