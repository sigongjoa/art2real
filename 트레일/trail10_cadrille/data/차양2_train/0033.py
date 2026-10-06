import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-98,-1),(-14,-72)).segment((14,-72)).segment((98,-1)).segment((85,26)).segment((0,-45)).segment((-85,26)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(10,200,14).translate((-31,0,17)))