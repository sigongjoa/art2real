import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-67,6),(-11,-35)).segment((11,-35)).segment((67,6)).segment((58,25)).segment((0,-16)).segment((-58,25)).close().assemble().finalize().extrude(22).cut(cq.Workplane('XY').box(6,200,12).translate((-23,0,11))).cut(cq.Workplane('XY').box(5,200,10).translate((28,0,11)))