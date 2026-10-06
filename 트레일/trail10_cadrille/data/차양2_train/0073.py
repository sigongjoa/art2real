import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-86,-4),(-12,-49)).segment((12,-49)).segment((86,-4)).segment((71,26)).segment((0,-19)).segment((-71,26)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(10,200,8).translate((21,0,13))).cut(cq.Workplane('XY').box(5,200,10).translate((-3,0,13)))