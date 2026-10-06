import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-96,19),(-18,-47)).segment((18,-47)).segment((96,19)).segment((81,50)).segment((0,-16)).segment((-81,50)).close().assemble().finalize().extrude(32).cut(cq.Workplane('XY').box(9,200,24).translate((22,0,16))).cut(cq.Workplane('XY').box(6,200,8).translate((31,0,16)))