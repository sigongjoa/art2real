import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-92,4),(-8,-50)).segment((8,-50)).segment((92,4)).segment((82,24)).segment((0,-30)).segment((-82,24)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(6,200,12).translate((0,0,13)))