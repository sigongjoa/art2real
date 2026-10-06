import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-94,11),(-17,-71)).segment((17,-71)).segment((94,11)).segment((76,48)).segment((0,-34)).segment((-76,48)).close().assemble().finalize().extrude(33).cut(cq.Workplane('XY').box(8,200,16).translate((32,0,17))).cut(cq.Workplane('XY').box(5,200,26).translate((20,0,17)))