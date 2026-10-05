import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-85,2),(-10,-55)).segment((10,-55)).segment((85,2)).segment((73,27)).segment((0,-30)).segment((-73,27)).close().assemble().finalize().extrude(20).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(3,200,8).translate((-15,0,10)))