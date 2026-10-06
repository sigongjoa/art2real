import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-93,17),(-17,-50)).segment((17,-50)).segment((93,17)).segment((75,53)).segment((0,-14)).segment((-75,53)).close().assemble().finalize().extrude(36).cut(cq.Workplane('XY').box(10,200,14).translate((-12,0,18))).cut(cq.Workplane('XY').box(9,200,16).translate((-14,0,18)))