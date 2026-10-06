import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-87,3),(-17,-61)).segment((17,-61)).segment((87,3)).segment((69,40)).segment((0,-24)).segment((-69,40)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(10,200,36).translate((35,0,21)))