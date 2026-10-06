import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-88,9),(-6,-61)).segment((6,-61)).segment((88,9)).segment((76,33)).segment((0,-37)).segment((-76,33)).close().assemble().finalize().extrude(44).cut(cq.Workplane('XY').box(7,200,24).translate((-18,0,22)))