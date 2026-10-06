import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-97,15),(-8,-61)).segment((8,-61)).segment((97,15)).segment((80,50)).segment((0,-26)).segment((-80,50)).close().assemble().finalize().extrude(40).cut(cq.Workplane('XY').box(9,200,40).translate((0,0,20)))