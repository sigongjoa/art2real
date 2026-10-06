import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-93,5),(-14,-55)).segment((14,-55)).segment((93,5)).segment((77,38)).segment((0,-22)).segment((-77,38)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(10)