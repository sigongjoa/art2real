import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-86,24),(-11,-49)).segment((11,-49)).segment((86,24)).segment((68,60)).segment((0,-13)).segment((-68,60)).close().assemble().finalize().extrude(44)