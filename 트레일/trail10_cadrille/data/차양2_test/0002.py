import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-98,1),(-16,-61)).segment((16,-61)).segment((98,1)).segment((84,30)).segment((0,-32)).segment((-84,30)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(12,200,34).translate((27,0,17)))