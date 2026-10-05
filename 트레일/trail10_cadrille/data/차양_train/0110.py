import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-93,2),(-6,-40)).segment((6,-40)).segment((93,2)).segment((84,21)).segment((0,-21)).segment((-84,21)).close().assemble().finalize().extrude(15).cut(cq.Workplane('XY').box(4,200,6).translate((21,0,8))).cut(cq.Workplane('XY').box(5,200,14).translate((17,0,8)))