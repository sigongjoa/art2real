import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-80,14),(-8,-28)).segment((8,-28)).segment((80,14)).segment((72,30)).segment((0,-12)).segment((-72,30)).close().assemble().finalize().extrude(19)