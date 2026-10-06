import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-93,3),(-11,-71)).segment((11,-71)).segment((93,3)).segment((76,38)).segment((0,-36)).segment((-76,38)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(6,200,16).translate((-30,0,17))).cut(cq.Workplane('XY').box(11,200,8).translate((-42,0,17)))