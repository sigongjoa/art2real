import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-71,-5),(-14,-40)).segment((14,-40)).segment((71,-5)).segment((58,21)).segment((0,-14)).segment((-58,21)).close().assemble().finalize().extrude(23)