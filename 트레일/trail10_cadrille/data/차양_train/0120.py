import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-88,10),(-10,-33)).segment((10,-33)).segment((88,10)).segment((80,26)).segment((0,-17)).segment((-80,26)).close().assemble().finalize().extrude(13)