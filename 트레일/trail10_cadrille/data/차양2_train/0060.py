import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-98,22),(-11,-73)).segment((11,-73)).segment((98,22)).segment((80,58)).segment((0,-37)).segment((-80,58)).close().assemble().finalize().extrude(37).cut(cq.Workplane('XY').box(6,200,16).translate((-25,0,19)))