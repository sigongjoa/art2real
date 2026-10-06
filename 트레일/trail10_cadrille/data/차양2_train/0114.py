import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-95,20),(-14,-66)).segment((14,-66)).segment((95,20)).segment((83,44)).segment((0,-42)).segment((-83,44)).close().assemble().finalize().extrude(24).cut(cq.Workplane('XY').box(6,200,20).translate((0,0,12)))