import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-87,8),(-14,-32)).segment((14,-32)).segment((87,8)).segment((78,26)).segment((0,-14)).segment((-78,26)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(5)