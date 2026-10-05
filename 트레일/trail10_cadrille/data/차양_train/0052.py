import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-68,7),(-8,-43)).segment((8,-43)).segment((68,7)).segment((60,24)).segment((0,-26)).segment((-60,24)).close().assemble().finalize().extrude(13)