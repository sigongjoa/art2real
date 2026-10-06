import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-85,17),(-16,-54)).segment((16,-54)).segment((85,17)).segment((67,53)).segment((0,-18)).segment((-67,53)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(8)