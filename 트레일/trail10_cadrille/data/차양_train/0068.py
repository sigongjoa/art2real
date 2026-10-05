import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-75,-2),(-4,-40)).segment((4,-40)).segment((75,-2)).segment((67,14)).segment((0,-24)).segment((-67,14)).close().assemble().finalize().extrude(11)