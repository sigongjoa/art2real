import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-87,4),(-8,-56)).segment((8,-56)).segment((87,4)).segment((74,30)).segment((0,-30)).segment((-74,30)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(12,200,28).translate((-7,0,15)))