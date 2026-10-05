import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-78,-3),(-14,-43)).segment((14,-43)).segment((78,-3)).segment((68,18)).segment((0,-22)).segment((-68,18)).close().assemble().finalize().extrude(12).cut(cq.Workplane('XY').box(7,200,6).translate((3,0,6))).cut(cq.Workplane('XY').box(5,200,10).translate((-19,0,6)))