import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-97,8),(-16,-54)).segment((16,-54)).segment((97,8)).segment((77,48)).segment((0,-14)).segment((-77,48)).close().assemble().finalize().extrude(35).cut(cq.Workplane('XY').box(12,200,28).translate((0,0,18)))