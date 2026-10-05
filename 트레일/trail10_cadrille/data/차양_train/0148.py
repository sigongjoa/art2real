import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-73,20),(-13,-50)).segment((13,-50)).segment((73,20)).segment((62,43)).segment((0,-27)).segment((-62,43)).close().assemble().finalize().extrude(13).cut(cq.Workplane('XY').box(7,200,6).translate((-5,0,7))).cut(cq.Workplane('XY').box(5,200,8).translate((-31,0,7)))