import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-84,19),(-13,-25)).segment((13,-25)).segment((84,19)).segment((74,39)).segment((0,-5)).segment((-74,39)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(7,200,20).translate((9,0,12))).cut(cq.Workplane('XY').box(3,200,20).translate((-36,0,12)))