import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-90,17),(-15,-50)).segment((15,-50)).segment((90,17)).segment((71,55)).segment((0,-12)).segment((-71,55)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(7,200,14).translate((-23,0,13))).cut(cq.Workplane('XY').box(8,200,24).translate((9,0,13)))