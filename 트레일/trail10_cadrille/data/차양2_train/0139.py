import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-96,20),(-18,-48)).segment((18,-48)).segment((96,20)).segment((81,50)).segment((0,-18)).segment((-81,50)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(7,200,40).translate((0,0,21)))