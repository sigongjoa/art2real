import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-92,3),(-18,-73)).segment((18,-73)).segment((92,3)).segment((79,30)).segment((0,-46)).segment((-79,30)).close().assemble().finalize().extrude(25)