import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-90,13),(-14,-46)).segment((14,-46)).segment((90,13)).segment((71,52)).segment((0,-7)).segment((-71,52)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(10,200,24).translate((12,0,12))).cut(cq.Workplane('XY').box(10,200,6).translate((-28,0,12)))