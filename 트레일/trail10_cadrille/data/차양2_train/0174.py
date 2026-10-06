import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-97,-4),(-17,-48)).segment((17,-48)).segment((97,-4)).segment((80,30)).segment((0,-14)).segment((-80,30)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(9,200,16).translate((0,0,14)))