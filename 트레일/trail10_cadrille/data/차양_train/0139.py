import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-90,15),(-11,-28)).segment((11,-28)).segment((90,15)).segment((77,42)).segment((0,-1)).segment((-77,42)).close().assemble().finalize().extrude(11).cut(cq.Workplane('XY').box(5,200,8).translate((-43,0,6)))