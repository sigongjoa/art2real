import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-97,21),(-6,-72)).segment((6,-72)).segment((97,21)).segment((81,53)).segment((0,-40)).segment((-81,53)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(9,200,12).translate((-48,0,13))).cut(cq.Workplane('XY').box(6,200,24).translate((-15,0,13)))