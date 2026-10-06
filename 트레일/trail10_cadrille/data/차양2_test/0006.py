import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-86,-4),(-14,-70)).segment((14,-70)).segment((86,-4)).segment((68,33)).segment((0,-33)).segment((-68,33)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(9,200,18).translate((-36,0,13)))