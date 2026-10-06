import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-94,-3),(-7,-61)).segment((7,-61)).segment((94,-3)).segment((76,33)).segment((0,-25)).segment((-76,33)).close().assemble().finalize().extrude(36).cut(cq.Workplane('XY').box(10,200,36).translate((0,0,18)))