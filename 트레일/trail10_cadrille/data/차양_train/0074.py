import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-84,4),(-4,-45)).segment((4,-45)).segment((84,4)).segment((70,32)).segment((0,-17)).segment((-70,32)).close().assemble().finalize().extrude(11).edges('>Z').chamfer(3)