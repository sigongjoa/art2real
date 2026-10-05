import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-93,-2),(-5,-45)).segment((5,-45)).segment((93,-2)).segment((85,15)).segment((0,-28)).segment((-85,15)).close().assemble().finalize().extrude(23).cut(cq.Workplane('XY').box(5,200,18).translate((-5,0,12)))