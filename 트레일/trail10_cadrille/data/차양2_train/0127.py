import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-91,9),(-15,-69)).segment((15,-69)).segment((91,9)).segment((78,36)).segment((0,-42)).segment((-78,36)).close().assemble().finalize().extrude(44).edges('>Z').chamfer(6)