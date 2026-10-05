import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-84,-3),(-5,-44)).segment((5,-44)).segment((84,-3)).segment((71,24)).segment((0,-17)).segment((-71,24)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(4,200,24).translate((0,0,13)))