import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-92,-4),(-10,-62)).segment((10,-62)).segment((92,-4)).segment((72,36)).segment((0,-22)).segment((-72,36)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(5,200,14).translate((11,0,22))).cut(cq.Workplane('XY').box(9,200,20).translate((16,0,22)))