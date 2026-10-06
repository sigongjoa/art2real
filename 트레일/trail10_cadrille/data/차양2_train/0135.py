import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-98,-1),(-9,-57)).segment((9,-57)).segment((98,-1)).segment((82,32)).segment((0,-24)).segment((-82,32)).close().assemble().finalize().extrude(36).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(7,200,28).translate((0,0,18)))