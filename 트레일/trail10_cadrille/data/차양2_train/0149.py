import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-94,13),(-12,-49)).segment((12,-49)).segment((94,13)).segment((81,40)).segment((0,-22)).segment((-81,40)).close().assemble().finalize().extrude(34).cut(cq.Workplane('XY').box(10,200,32).translate((-1,0,17))).cut(cq.Workplane('XY').box(10,200,6).translate((-14,0,17)))