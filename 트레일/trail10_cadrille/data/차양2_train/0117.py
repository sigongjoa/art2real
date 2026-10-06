import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-94,11),(-18,-49)).segment((18,-49)).segment((94,11)).segment((74,51)).segment((0,-9)).segment((-74,51)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(8,200,34).translate((42,0,18))).cut(cq.Workplane('XY').box(8,200,8).translate((32,0,18)))