import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-96,10),(-17,-71)).segment((17,-71)).segment((96,10)).segment((78,46)).segment((0,-35)).segment((-78,46)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(5,200,12).translate((-19,0,19)))