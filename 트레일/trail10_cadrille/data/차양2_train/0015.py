import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-93,-5),(-16,-65)).segment((16,-65)).segment((93,-5)).segment((75,31)).segment((0,-29)).segment((-75,31)).close().assemble().finalize().extrude(42).cut(cq.Workplane('XY').box(9,200,14).translate((-40,0,21))).cut(cq.Workplane('XY').box(5,200,24).translate((-20,0,21)))