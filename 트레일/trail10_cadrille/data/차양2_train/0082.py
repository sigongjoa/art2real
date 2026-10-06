import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-94,24),(-8,-49)).segment((8,-49)).segment((94,24)).segment((81,51)).segment((0,-22)).segment((-81,51)).close().assemble().finalize().extrude(37)