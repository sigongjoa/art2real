import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-95,3),(-14,-55)).segment((14,-55)).segment((95,3)).segment((83,27)).segment((0,-31)).segment((-83,27)).close().assemble().finalize().extrude(34)