import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-88,16),(-10,-53)).segment((10,-53)).segment((88,16)).segment((71,50)).segment((0,-19)).segment((-71,50)).close().assemble().finalize().extrude(43).cut(cq.Workplane('XY').box(6,200,26).translate((-42,0,22))).cut(cq.Workplane('XY').box(7,200,12).translate((0,0,22)))