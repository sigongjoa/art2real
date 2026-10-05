import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-95,11),(-5,-43)).segment((5,-43)).segment((95,11)).segment((83,35)).segment((0,-19)).segment((-83,35)).close().assemble().finalize().extrude(12).cut(cq.Workplane('XY').box(7,200,12).translate((-26,0,6)))