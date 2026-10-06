import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-98,20),(-16,-47)).segment((16,-47)).segment((98,20)).segment((83,50)).segment((0,-17)).segment((-83,50)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(11)