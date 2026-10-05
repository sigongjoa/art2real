import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-71,-3),(-11,-49)).segment((11,-49)).segment((71,-3)).segment((59,21)).segment((0,-25)).segment((-59,21)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(6,200,6).translate((32,0,12))).cut(cq.Workplane('XY').box(5,200,10).translate((14,0,12)))