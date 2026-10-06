import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-91,18),(-8,-62)).segment((8,-62)).segment((91,18)).segment((72,56)).segment((0,-24)).segment((-72,56)).close().assemble().finalize().extrude(42).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,40).translate((10,0,21)))