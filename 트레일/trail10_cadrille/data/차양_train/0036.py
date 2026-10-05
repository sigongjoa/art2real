import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-87,20),(-5,-49)).segment((5,-49)).segment((87,20)).segment((78,39)).segment((0,-30)).segment((-78,39)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(4,200,10).translate((0,0,13)))