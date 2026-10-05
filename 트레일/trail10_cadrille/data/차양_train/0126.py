import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-57,17),(-4,-45)).segment((4,-45)).segment((57,17)).segment((45,42)).segment((0,-20)).segment((-45,42)).close().assemble().finalize().extrude(11).cut(cq.Workplane('XY').box(5,200,10).translate((19,0,6)))