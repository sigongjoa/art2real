import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-98,8),(-17,-57)).segment((17,-57)).segment((98,8)).segment((86,32)).segment((0,-33)).segment((-86,32)).close().assemble().finalize().extrude(38).edges('>Z').chamfer(8)