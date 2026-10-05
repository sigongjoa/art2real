import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-71,-2),(-4,-30)).segment((4,-30)).segment((71,-2)).segment((63,14)).segment((0,-14)).segment((-63,14)).close().assemble().finalize().extrude(16)