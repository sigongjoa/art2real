import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-92,11),(-18,-66)).segment((18,-66)).segment((92,11)).segment((79,38)).segment((0,-39)).segment((-79,38)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(5,200,20).translate((0,0,15)))