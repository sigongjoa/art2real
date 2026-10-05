import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-70,-5),(-5,-41)).segment((5,-41)).segment((70,-5)).segment((58,19)).segment((0,-17)).segment((-58,19)).close().assemble().finalize().extrude(11).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(5,200,8).translate((31,0,6))).cut(cq.Workplane('XY').box(3,200,6).translate((28,0,6)))