import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-89,-3),(-18,-72)).segment((18,-72)).segment((89,-3)).segment((70,35)).segment((0,-34)).segment((-70,35)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(10,200,24).translate((-40,0,18))).cut(cq.Workplane('XY').box(7,200,24).translate((-2,0,18)))