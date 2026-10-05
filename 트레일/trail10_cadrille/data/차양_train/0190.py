import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-77,13),(-11,-26)).segment((11,-26)).segment((77,13)).segment((70,28)).segment((0,-11)).segment((-70,28)).close().assemble().finalize().extrude(16).cut(cq.Workplane('XY').box(4,200,6).translate((0,0,8)))