import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-88,2),(-7,-33)).segment((7,-33)).segment((88,2)).segment((80,18)).segment((0,-17)).segment((-80,18)).close().assemble().finalize().extrude(22).cut(cq.Workplane('XY').box(3,200,16).translate((13,0,11)))