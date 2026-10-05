import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-78,12),(-12,-43)).segment((12,-43)).segment((78,12)).segment((70,29)).segment((0,-26)).segment((-70,29)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(3,200,22).translate((5,0,12))).cut(cq.Workplane('XY').box(7,200,16).translate((30,0,12)))