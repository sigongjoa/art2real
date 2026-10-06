import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-95,23),(-15,-65)).segment((15,-65)).segment((95,23)).segment((83,48)).segment((0,-40)).segment((-83,48)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(12,200,20).translate((-5,0,19)))