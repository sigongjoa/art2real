import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-85,11),(-17,-53)).segment((17,-53)).segment((85,11)).segment((72,38)).segment((0,-26)).segment((-72,38)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(10)