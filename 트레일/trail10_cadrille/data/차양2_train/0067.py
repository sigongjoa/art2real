import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-98,15),(-18,-69)).segment((18,-69)).segment((98,15)).segment((84,43)).segment((0,-41)).segment((-84,43)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(7)