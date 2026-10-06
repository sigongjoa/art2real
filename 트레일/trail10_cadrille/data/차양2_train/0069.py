import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-98,-4),(-18,-49)).segment((18,-49)).segment((98,-4)).segment((82,28)).segment((0,-17)).segment((-82,28)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(8)