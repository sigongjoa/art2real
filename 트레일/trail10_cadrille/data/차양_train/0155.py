import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-67,6),(-13,-32)).segment((13,-32)).segment((67,6)).segment((55,30)).segment((0,-8)).segment((-55,30)).close().assemble().finalize().extrude(12).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(7,200,8).translate((-29,0,6))).cut(cq.Workplane('XY').box(5,200,12).translate((-16,0,6)))