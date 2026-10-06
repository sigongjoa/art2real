import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-93,3),(-6,-66)).segment((6,-66)).segment((93,3)).segment((75,40)).segment((0,-29)).segment((-75,40)).close().assemble().finalize().extrude(33).cut(cq.Workplane('XY').box(8,200,32).translate((-33,0,17))).cut(cq.Workplane('XY').box(9,200,18).translate((30,0,17)))