import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-61,2),(-12,-38)).segment((12,-38)).segment((61,2)).segment((50,24)).segment((0,-16)).segment((-50,24)).close().assemble().finalize().extrude(16).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(7,200,12).translate((30,0,8))).cut(cq.Workplane('XY').box(4,200,16).translate((-25,0,8)))