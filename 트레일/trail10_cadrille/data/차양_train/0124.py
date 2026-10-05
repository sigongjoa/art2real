import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-89,-5),(-14,-55)).segment((14,-55)).segment((89,-5)).segment((75,23)).segment((0,-27)).segment((-75,23)).close().assemble().finalize().extrude(14).edges('>Z').chamfer(6)