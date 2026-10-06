import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-89,13),(-11,-57)).segment((11,-57)).segment((89,13)).segment((76,40)).segment((0,-30)).segment((-76,40)).close().assemble().finalize().extrude(37).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(9,200,30).translate((5,0,19))).cut(cq.Workplane('XY').box(10,200,16).translate((39,0,19)))