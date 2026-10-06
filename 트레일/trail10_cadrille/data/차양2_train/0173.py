import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-90,8),(-6,-55)).segment((6,-55)).segment((90,8)).segment((77,35)).segment((0,-28)).segment((-77,35)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(7,200,24).translate((0,0,21)))