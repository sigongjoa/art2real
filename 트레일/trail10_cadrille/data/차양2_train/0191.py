import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-93,16),(-15,-55)).segment((15,-55)).segment((93,16)).segment((77,49)).segment((0,-22)).segment((-77,49)).close().assemble().finalize().extrude(34)