import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-85,1),(-18,-50)).segment((18,-50)).segment((85,1)).segment((68,35)).segment((0,-16)).segment((-68,35)).close().assemble().finalize().extrude(42).cut(cq.Workplane('XY').box(9,200,12).translate((0,0,21)))