import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-88,20),(-9,-48)).segment((9,-48)).segment((88,20)).segment((76,45)).segment((0,-23)).segment((-76,45)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(9).cut(cq.Workplane('XY').box(10,200,20).translate((0,0,12)))