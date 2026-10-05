import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-68,13),(-13,-29)).segment((13,-29)).segment((68,13)).segment((60,29)).segment((0,-13)).segment((-60,29)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(5,200,10).translate((12,0,7))).cut(cq.Workplane('XY').box(3,200,6).translate((13,0,7)))