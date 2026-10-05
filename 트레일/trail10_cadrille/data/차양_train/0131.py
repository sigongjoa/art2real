import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-62,-5),(-7,-43)).segment((7,-43)).segment((62,-5)).segment((52,16)).segment((0,-22)).segment((-52,16)).close().assemble().finalize().extrude(22).cut(cq.Workplane('XY').box(4,200,8).translate((0,0,11)))