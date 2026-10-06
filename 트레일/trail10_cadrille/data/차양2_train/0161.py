import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-89,19),(-15,-63)).segment((15,-63)).segment((89,19)).segment((71,55)).segment((0,-27)).segment((-71,55)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(9)