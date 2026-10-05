import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-92,13),(-6,-39)).segment((6,-39)).segment((92,13)).segment((78,41)).segment((0,-11)).segment((-78,41)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(6,200,10).translate((45,0,9)))