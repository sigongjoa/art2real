import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-94,-2),(-9,-59)).segment((9,-59)).segment((94,-2)).segment((78,30)).segment((0,-27)).segment((-78,30)).close().assemble().finalize().extrude(43).cut(cq.Workplane('XY').box(10,200,22).translate((37,0,22))).cut(cq.Workplane('XY').box(8,200,24).translate((-24,0,22)))