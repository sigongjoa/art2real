import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-92,-1),(-16,-65)).segment((16,-65)).segment((92,-1)).segment((76,31)).segment((0,-33)).segment((-76,31)).close().assemble().finalize().extrude(30).cut(cq.Workplane('XY').box(9,200,14).translate((-4,0,15))).cut(cq.Workplane('XY').box(8,200,12).translate((36,0,15)))