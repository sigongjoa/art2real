import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-85,11),(-18,-68)).segment((18,-68)).segment((85,11)).segment((69,44)).segment((0,-35)).segment((-69,44)).close().assemble().finalize().extrude(30)