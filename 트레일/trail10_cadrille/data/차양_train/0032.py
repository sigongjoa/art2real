import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-67,6),(-8,-32)).segment((8,-32)).segment((67,6)).segment((60,21)).segment((0,-17)).segment((-60,21)).close().assemble().finalize().extrude(12).cut(cq.Workplane('XY').box(8,200,10).translate((-23,0,6))).cut(cq.Workplane('XY').box(6,200,10).translate((-5,0,6)))