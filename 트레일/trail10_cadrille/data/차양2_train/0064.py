import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-95,3),(-15,-71)).segment((15,-71)).segment((95,3)).segment((82,30)).segment((0,-44)).segment((-82,30)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(11,200,10).translate((0,0,15)))