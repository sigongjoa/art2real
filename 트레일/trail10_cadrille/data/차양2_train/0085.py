import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-94,23),(-17,-56)).segment((17,-56)).segment((94,23)).segment((75,62)).segment((0,-17)).segment((-75,62)).close().assemble().finalize().extrude(33).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(11,200,20).translate((-17,0,17))).cut(cq.Workplane('XY').box(10,200,22).translate((39,0,17)))