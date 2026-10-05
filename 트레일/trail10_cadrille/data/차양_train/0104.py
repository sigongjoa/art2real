import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-68,15),(-10,-46)).segment((10,-46)).segment((68,15)).segment((61,30)).segment((0,-31)).segment((-61,30)).close().assemble().finalize().extrude(13).cut(cq.Workplane('XY').box(6,200,6).translate((29,0,7)))