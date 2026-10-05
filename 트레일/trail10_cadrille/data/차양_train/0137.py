import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-89,12),(-6,-54)).segment((6,-54)).segment((89,12)).segment((81,28)).segment((0,-38)).segment((-81,28)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(3,200,22).translate((0,0,11)))