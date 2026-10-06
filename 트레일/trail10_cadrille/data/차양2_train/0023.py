import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-94,2),(-10,-62)).segment((10,-62)).segment((94,2)).segment((81,28)).segment((0,-36)).segment((-81,28)).close().assemble().finalize().extrude(35)