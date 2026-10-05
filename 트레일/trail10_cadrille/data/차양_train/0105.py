import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-93,10),(-6,-52)).segment((6,-52)).segment((93,10)).segment((86,25)).segment((0,-37)).segment((-86,25)).close().assemble().finalize().extrude(22).cut(cq.Workplane('XY').box(5,200,18).translate((0,0,11)))