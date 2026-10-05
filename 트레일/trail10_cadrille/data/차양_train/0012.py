import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-90,3),(-14,-50)).segment((14,-50)).segment((90,3)).segment((83,17)).segment((0,-36)).segment((-83,17)).close().assemble().finalize().extrude(12).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(5,200,8).translate((-44,0,6))).cut(cq.Workplane('XY').box(3,200,8).translate((-11,0,6)))