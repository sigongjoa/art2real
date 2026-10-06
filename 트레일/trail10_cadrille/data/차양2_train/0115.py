import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-85,8),(-10,-69)).segment((10,-69)).segment((85,8)).segment((67,45)).segment((0,-32)).segment((-67,45)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(12)