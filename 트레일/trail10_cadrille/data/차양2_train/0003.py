import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-95,22),(-7,-68)).segment((7,-68)).segment((95,22)).segment((79,55)).segment((0,-35)).segment((-79,55)).close().assemble().finalize().extrude(34).cut(cq.Workplane('XY').box(8,200,14).translate((16,0,17))).cut(cq.Workplane('XY').box(12,200,32).translate((-12,0,17)))