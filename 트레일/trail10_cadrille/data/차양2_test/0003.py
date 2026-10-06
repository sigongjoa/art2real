import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-96,18),(-8,-74)).segment((8,-74)).segment((96,18)).segment((79,53)).segment((0,-39)).segment((-79,53)).close().assemble().finalize().extrude(44).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(5,200,20).translate((-47,0,22))).cut(cq.Workplane('XY').box(8,200,30).translate((-34,0,22)))