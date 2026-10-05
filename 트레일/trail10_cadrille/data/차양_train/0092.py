import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-89,1),(-11,-54)).segment((11,-54)).segment((89,1)).segment((76,27)).segment((0,-28)).segment((-76,27)).close().assemble().finalize().extrude(12).cut(cq.Workplane('XY').box(3,200,12).translate((0,0,6)))