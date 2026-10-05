import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-65,17),(-5,-41)).segment((5,-41)).segment((65,17)).segment((57,33)).segment((0,-25)).segment((-57,33)).close().assemble().finalize().extrude(22).cut(cq.Workplane('XY').box(7,200,12).translate((-7,0,11)))