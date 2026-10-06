import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-87,1),(-10,-62)).segment((10,-62)).segment((87,1)).segment((71,33)).segment((0,-30)).segment((-71,33)).close().assemble().finalize().extrude(42).cut(cq.Workplane('XY').box(10,200,36).translate((-23,0,21))).cut(cq.Workplane('XY').box(6,200,18).translate((9,0,21)))