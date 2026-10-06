import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-96,20),(-15,-61)).segment((15,-61)).segment((96,20)).segment((77,59)).segment((0,-22)).segment((-77,59)).close().assemble().finalize().extrude(42).cut(cq.Workplane('XY').box(12,200,36).translate((28,0,21))).cut(cq.Workplane('XY').box(9,200,38).translate((-27,0,21)))