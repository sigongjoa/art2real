import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-92,1),(-8,-37)).segment((8,-37)).segment((92,1)).segment((82,22)).segment((0,-16)).segment((-82,22)).close().assemble().finalize().extrude(20).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(3,200,6).translate((-41,0,10)))