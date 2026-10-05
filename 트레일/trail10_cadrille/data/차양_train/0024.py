import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-73,14),(-11,-32)).segment((11,-32)).segment((73,14)).segment((60,40)).segment((0,-6)).segment((-60,40)).close().assemble().finalize().extrude(14).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(3,200,12).translate((0,0,7)))