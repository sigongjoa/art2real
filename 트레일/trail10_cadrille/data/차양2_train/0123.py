import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-92,12),(-15,-57)).segment((15,-57)).segment((92,12)).segment((79,39)).segment((0,-30)).segment((-79,39)).close().assemble().finalize().extrude(39).cut(cq.Workplane('XY').box(11,200,32).translate((0,0,20)))