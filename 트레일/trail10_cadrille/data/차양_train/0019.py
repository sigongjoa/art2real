import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-68,13),(-6,-55)).segment((6,-55)).segment((68,13)).segment((58,34)).segment((0,-34)).segment((-58,34)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(7,200,26).translate((0,0,13)))