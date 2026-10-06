import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-98,16),(-16,-46)).segment((16,-46)).segment((98,16)).segment((83,47)).segment((0,-15)).segment((-83,47)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(11,200,16).translate((16,0,12))).cut(cq.Workplane('XY').box(10,200,12).translate((-28,0,12)))