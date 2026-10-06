import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-97,25),(-7,-49)).segment((7,-49)).segment((97,25)).segment((84,52)).segment((0,-22)).segment((-84,52)).close().assemble().finalize().extrude(37).cut(cq.Workplane('XY').box(11,200,12).translate((15,0,19)))