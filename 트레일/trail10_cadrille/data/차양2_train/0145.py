import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-85,25),(-6,-62)).segment((6,-62)).segment((85,25)).segment((66,64)).segment((0,-23)).segment((-66,64)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(9,200,10).translate((28,0,19)))