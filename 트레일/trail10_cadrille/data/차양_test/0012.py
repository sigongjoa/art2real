import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-91,-2),(-10,-48)).segment((10,-48)).segment((91,-2)).segment((82,17)).segment((0,-29)).segment((-82,17)).close().assemble().finalize().extrude(11).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(6,200,10).translate((-12,0,6))).cut(cq.Workplane('XY').box(4,200,6).translate((-5,0,6)))