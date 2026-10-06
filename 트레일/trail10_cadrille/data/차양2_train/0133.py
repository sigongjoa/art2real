import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-91,22),(-15,-67)).segment((15,-67)).segment((91,22)).segment((76,53)).segment((0,-36)).segment((-76,53)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(6,200,10).translate((0,0,14)))