import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-86,8),(-10,-58)).segment((10,-58)).segment((86,8)).segment((71,38)).segment((0,-28)).segment((-71,38)).close().assemble().finalize().extrude(35).cut(cq.Workplane('XY').box(9,200,24).translate((30,0,18))).cut(cq.Workplane('XY').box(7,200,16).translate((-11,0,18)))