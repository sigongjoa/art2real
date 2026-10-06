import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-94,-2),(-15,-63)).segment((15,-63)).segment((94,-2)).segment((82,23)).segment((0,-38)).segment((-82,23)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(5,200,28).translate((23,0,20)))