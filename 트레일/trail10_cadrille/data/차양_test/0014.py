import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-63,3),(-13,-55)).segment((13,-55)).segment((63,3)).segment((53,24)).segment((0,-34)).segment((-53,24)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(4,200,6).translate((19,0,8))).cut(cq.Workplane('XY').box(8,200,12).translate((22,0,8)))