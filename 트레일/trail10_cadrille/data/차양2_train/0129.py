import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-98,9),(-17,-54)).segment((17,-54)).segment((98,9)).segment((82,41)).segment((0,-22)).segment((-82,41)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(12,200,32).translate((32,0,19)))