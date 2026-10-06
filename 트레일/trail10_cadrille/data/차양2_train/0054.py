import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-97,22),(-18,-53)).segment((18,-53)).segment((97,22)).segment((83,51)).segment((0,-24)).segment((-83,51)).close().assemble().finalize().extrude(26)