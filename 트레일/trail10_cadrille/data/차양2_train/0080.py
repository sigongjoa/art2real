import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-86,5),(-18,-49)).segment((18,-49)).segment((86,5)).segment((69,39)).segment((0,-15)).segment((-69,39)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(10,200,34).translate((0,0,17)))