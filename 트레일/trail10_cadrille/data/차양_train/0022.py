import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-61,7),(-12,-51)).segment((12,-51)).segment((61,7)).segment((47,35)).segment((0,-23)).segment((-47,35)).close().assemble().finalize().extrude(21).cut(cq.Workplane('XY').box(7,200,12).translate((18,0,11))).cut(cq.Workplane('XY').box(8,200,6).translate((-27,0,11)))