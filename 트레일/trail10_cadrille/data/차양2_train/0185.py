import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-90,-4),(-10,-69)).segment((10,-69)).segment((90,-4)).segment((75,27)).segment((0,-38)).segment((-75,27)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(9,200,14).translate((0,0,21)))