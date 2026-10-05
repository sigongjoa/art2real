import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-64,-1),(-5,-51)).segment((5,-51)).segment((64,-1)).segment((55,18)).segment((0,-32)).segment((-55,18)).close().assemble().finalize().extrude(28).cut(cq.Workplane('XY').box(7,200,22).translate((-23,0,14))).cut(cq.Workplane('XY').box(7,200,8).translate((-4,0,14)))