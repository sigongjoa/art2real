import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-88,6),(-10,-52)).segment((10,-52)).segment((88,6)).segment((75,32)).segment((0,-26)).segment((-75,32)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(10,200,12).translate((-33,0,13))).cut(cq.Workplane('XY').box(9,200,6).translate((5,0,13)))