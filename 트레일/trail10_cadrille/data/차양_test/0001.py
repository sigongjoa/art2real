import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-67,3),(-4,-29)).segment((4,-29)).segment((67,3)).segment((56,26)).segment((0,-6)).segment((-56,26)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(3,200,10).translate((17,0,9)))