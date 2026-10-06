import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-90,16),(-18,-55)).segment((18,-55)).segment((90,16)).segment((75,47)).segment((0,-24)).segment((-75,47)).close().assemble().finalize().extrude(38).cut(cq.Workplane('XY').box(8,200,32).translate((0,0,19)))