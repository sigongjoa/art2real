import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-94,3),(-7,-57)).segment((7,-57)).segment((94,3)).segment((80,31)).segment((0,-29)).segment((-80,31)).close().assemble().finalize().extrude(38).cut(cq.Workplane('XY').box(5,200,38).translate((-43,0,19)))