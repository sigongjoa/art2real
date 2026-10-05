import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-72,13),(-14,-50)).segment((14,-50)).segment((72,13)).segment((58,41)).segment((0,-22)).segment((-58,41)).close().assemble().finalize().extrude(21).cut(cq.Workplane('XY').box(3,200,16).translate((-6,0,11)))