import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-66,-3),(-13,-49)).segment((13,-49)).segment((66,-3)).segment((53,24)).segment((0,-22)).segment((-53,24)).close().assemble().finalize().extrude(10).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(4,200,8).translate((5,0,5))).cut(cq.Workplane('XY').box(6,200,6).translate((0,0,5)))