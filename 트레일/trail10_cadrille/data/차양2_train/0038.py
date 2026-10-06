import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-92,0),(-11,-45)).segment((11,-45)).segment((92,0)).segment((72,40)).segment((0,-5)).segment((-72,40)).close().assemble().finalize().extrude(40).cut(cq.Workplane('XY').box(8,200,20).translate((41,0,20))).cut(cq.Workplane('XY').box(12,200,36).translate((-6,0,20)))