import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-64,16),(-4,-53)).segment((4,-53)).segment((64,16)).segment((53,38)).segment((0,-31)).segment((-53,38)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(3)