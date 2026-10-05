import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-87,8),(-8,-29)).segment((8,-29)).segment((87,8)).segment((78,26)).segment((0,-11)).segment((-78,26)).close().assemble().finalize().extrude(25).cut(cq.Workplane('XY').box(6,200,16).translate((0,0,13)))