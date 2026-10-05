import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-85,3),(-13,-50)).segment((13,-50)).segment((85,3)).segment((72,30)).segment((0,-23)).segment((-72,30)).close().assemble().finalize().extrude(20).cut(cq.Workplane('XY').box(8,200,6).translate((-12,0,10)))