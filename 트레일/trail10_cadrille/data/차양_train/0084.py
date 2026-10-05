import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-75,8),(-6,-28)).segment((6,-28)).segment((75,8)).segment((66,27)).segment((0,-9)).segment((-66,27)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(5,200,16).translate((0,0,14)))