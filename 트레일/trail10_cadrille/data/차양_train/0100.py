import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-86,7),(-10,-55)).segment((10,-55)).segment((86,7)).segment((74,32)).segment((0,-30)).segment((-74,32)).close().assemble().finalize().extrude(12).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(3,200,6).translate((0,0,6)))