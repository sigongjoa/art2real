import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-86,19),(-17,-45)).segment((17,-45)).segment((86,19)).segment((69,54)).segment((0,-10)).segment((-69,54)).close().assemble().finalize().extrude(32).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(8,200,22).translate((-31,0,16)))