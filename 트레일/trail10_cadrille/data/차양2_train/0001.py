import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-90,-5),(-16,-45)).segment((16,-45)).segment((90,-5)).segment((78,19)).segment((0,-21)).segment((-78,19)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(8,200,34).translate((-42,0,21)))