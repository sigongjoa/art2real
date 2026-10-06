import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-87,-2),(-11,-56)).segment((11,-56)).segment((87,-2)).segment((69,34)).segment((0,-20)).segment((-69,34)).close().assemble().finalize().extrude(40).cut(cq.Workplane('XY').box(12,200,14).translate((0,0,20)))