import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-55,-2),(-8,-42)).segment((8,-42)).segment((55,-2)).segment((42,25)).segment((0,-15)).segment((-42,25)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(8,200,24).translate((6,0,13)))