import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-88,8),(-14,-67)).segment((14,-67)).segment((88,8)).segment((71,42)).segment((0,-33)).segment((-71,42)).close().assemble().finalize().extrude(43).cut(cq.Workplane('XY').box(5,200,10).translate((-16,0,22)))