import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-58,10),(-10,-42)).segment((10,-42)).segment((58,10)).segment((51,24)).segment((0,-28)).segment((-51,24)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(5,200,6).translate((6,0,10)))