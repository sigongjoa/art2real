import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-97,1),(-6,-62)).segment((6,-62)).segment((97,1)).segment((79,38)).segment((0,-25)).segment((-79,38)).close().assemble().finalize().extrude(39).cut(cq.Workplane('XY').box(12,200,28).translate((3,0,20)))