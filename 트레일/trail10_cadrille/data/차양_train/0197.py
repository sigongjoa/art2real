import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-77,9),(-5,-53)).segment((5,-53)).segment((77,9)).segment((63,37)).segment((0,-25)).segment((-63,37)).close().assemble().finalize().extrude(14)