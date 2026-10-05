import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-62,18),(-12,-43)).segment((12,-43)).segment((62,18)).segment((55,32)).segment((0,-29)).segment((-55,32)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(5,200,14).translate((0,0,10)))