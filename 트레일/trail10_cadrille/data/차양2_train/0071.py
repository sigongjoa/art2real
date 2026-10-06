import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-85,24),(-11,-63)).segment((11,-63)).segment((85,24)).segment((71,53)).segment((0,-34)).segment((-71,53)).close().assemble().finalize().extrude(37)