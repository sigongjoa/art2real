import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-90,24),(-8,-60)).segment((8,-60)).segment((90,24)).segment((77,51)).segment((0,-33)).segment((-77,51)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(12,200,16).translate((18,0,13)))