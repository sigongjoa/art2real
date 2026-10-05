import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-57,8),(-11,-52)).segment((11,-52)).segment((57,8)).segment((44,35)).segment((0,-25)).segment((-44,35)).close().assemble().finalize().extrude(16).cut(cq.Workplane('XY').box(7,200,10).translate((-5,0,8)))