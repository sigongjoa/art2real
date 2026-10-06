import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-89,9),(-8,-63)).segment((8,-63)).segment((89,9)).segment((77,33)).segment((0,-39)).segment((-77,33)).close().assemble().finalize().extrude(28).cut(cq.Workplane('XY').box(8,200,22).translate((0,0,14)))