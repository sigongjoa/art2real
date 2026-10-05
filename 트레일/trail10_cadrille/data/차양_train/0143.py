import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-72,9),(-6,-43)).segment((6,-43)).segment((72,9)).segment((65,23)).segment((0,-29)).segment((-65,23)).close().assemble().finalize().extrude(14).cut(cq.Workplane('XY').box(7,200,14).translate((0,0,7)))