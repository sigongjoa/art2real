import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-67,13),(-14,-49)).segment((14,-49)).segment((67,13)).segment((57,33)).segment((0,-29)).segment((-57,33)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(4,200,22).translate((0,0,13)))