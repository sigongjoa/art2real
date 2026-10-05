import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-63,15),(-5,-55)).segment((5,-55)).segment((63,15)).segment((50,42)).segment((0,-28)).segment((-50,42)).close().assemble().finalize().extrude(13).cut(cq.Workplane('XY').box(3,200,8).translate((18,0,7)))